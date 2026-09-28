# Sheet Music Transcriber

Local web app: upload an audio or video file, pick an instrument, and get sheet music on screen plus MusicXML, MIDI, and PDF (via the browser's print dialog).

Pipeline: bundled ffmpeg (`imageio-ffmpeg`) pulls the audio out, a note detector turns it into notes, and music21 snaps them to the detected beats and writes the score. OpenSheetMusicDisplay renders it in the page.

Pick "Recording is" to match the file:

| Option | Use for | Note detector |
|---|---|---|
| Piano | Solo piano | Piano model (Kong et al.) |
| Solo instrument / voice | One instrument or voice, no backing | Basic Pitch |
| Song with backing: melody only | A lead line (violin, voice, flute) over drums, bass, piano or guitar | Demucs removes the backing, Basic Pitch scores every pitch frame by frame, and a Viterbi tracker follows one continuous line through it |

## Setup (Python 3.11; Basic Pitch doesn't support 3.14)

```
py -3.11 -m venv .venv
.venv\Scripts\pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
.venv\Scripts\pip install -r requirements.txt
curl.exe -L -o models\piano_note_pedal.pth "https://zenodo.org/record/4034264/files/CRNN_note_F1%3D0.9677_pedal_F1%3D0.9186.pth?download=1"
```

The last line downloads the 164 MB piano model (Kong et al., "High-resolution Piano Transcription with Pedals"), which is used when "Recording is: Piano" is selected. The first "Song with backing" run also downloads the Demucs `htdemucs_6s` model (about 50 MB) into the torch cache.

## Run

```
.venv\Scripts\python app.py
```

Open http://127.0.0.1:5000.

## Check

```
.venv\Scripts\python check_transcribe.py
```

## Limits

- Works best on one instrument or voice. For songs with backing, use "Song with backing: melody only". Demucs has no violin stem, so strings and pads that share the "other" stem can still leak into the melody.
- "Song with backing" takes about 1-1.5x the song's length on CPU (separation plus note detection).
- In "Song with backing" mode, the tracker penalises big jumps, and it writes rests only where the separated lead audio drops about 12 dB below its usual level. A very quiet passage can come out as rests, and a pad that keeps sounding through a real pause can still fill it.
- Notes more than a sixth above the surrounding melody are moved down an octave (this removes overtones). A real high note that far above its neighbours gets moved down too. Low notes are never moved up.
- A note that leaps 9 or more semitones away from both neighbours in the same direction (an up-down or down-up zigzag) is moved by an octave toward them; these come from the backing or an overtone. A real out-and-back leap that big is changed too, unless there's a pause of at least a quarter second on both sides.
- A held note is split wherever another pitch attacks and Basic Pitch rates it higher, so a fast figure over a sustained note isn't written as one long note. Figures faster than about 100 ms per note still get merged, and soft re-bows of the same pitch without a clear attack stay one note.
- Each beat uses either 16ths or triplets, never both, and gaps under half a beat are closed instead of written as rests. Very fast ornaments get simplified.
- Pedalled notes are notated only until the next note starts, so held bass octaves and melody notes over an arpeggio show up shorter than written.
- The grid follows the detected beats, so rubato stays aligned. Where the beat tracker slips, a few measures still get odd tuplets.
- The piano model runs on CPU at about 1.5x the recording's length (a 15-minute piece takes about 20 minutes). Trim long files first if you only need a section.
- Assumes 4/4 time. The tempo is auto-detected (you can override it), and the key is estimated.
- Non-piano instruments get a single melody line (the highest note at each moment), folded into the instrument's range. Bb/Eb instruments are written transposed.
- The page loads OpenSheetMusicDisplay from a CDN, so viewing needs internet. Downloads and transcription work offline.
