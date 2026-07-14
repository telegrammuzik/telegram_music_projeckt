"""
Ortak MIDI okuma/yazma araçları (Faz 0). pretty_midi/mido kullanmadan, saf
Python ile standart MIDI dosyaları üretir ve okur. Tüm fazlar (akorlar,
egzersizler, akort değişimi, doğaçlama backing vb.) bunu paylaşır.
"""

import struct

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def midi_to_name(n: int) -> str:
    return f"{NOTE_NAMES[n % 12]}{n // 12 - 1}"


def name_to_midi(name: str) -> int:
    """'C4', 'F#3', 'Bb2' gibi isimleri MIDI nota numarasına çevirir."""
    name = name.strip()
    if len(name) >= 2 and name[1] in ("#", "b"):
        letter = name[0].upper() + name[1]
        octave = int(name[2:])
    else:
        letter = name[0].upper()
        octave = int(name[1:])
    flat_map = {"Db": "C#", "Eb": "D#", "Gb": "F#", "Ab": "G#", "Bb": "A#"}
    letter = flat_map.get(letter, letter)
    idx = NOTE_NAMES.index(letter)
    return (octave + 1) * 12 + idx


def _write_vlq(value: int) -> bytes:
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(out)


def _read_vlq(data: bytes, i: int):
    value = 0
    while True:
        byte = data[i]
        i += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, i


class MidiNote:
    __slots__ = ("pitch", "start", "end", "velocity", "channel")

    def __init__(self, pitch, start, end, velocity=90, channel=0):
        self.pitch = pitch
        self.start = start
        self.end = end
        self.velocity = velocity
        self.channel = channel


def write_midi(tracks, output_path, ticks_per_beat=220, tempo_bpm=120):
    """
    tracks: [[MidiNote, ...], [MidiNote, ...], ...] — her alt liste ayrı bir
    MIDI kanalına/track'e yazılır (kanal = track index, 9 numara davul kanalı
    sayılır — GM standardına göre).
    """
    us_per_beat = int(60_000_000 / tempo_bpm)
    sec_per_tick = (us_per_beat / 1_000_000) / ticks_per_beat

    chunks = []
    for track_idx, notes in enumerate(tracks):
        events = []
        for n in notes:
            start_tick = int(round(n.start / sec_per_tick))
            end_tick = int(round(n.end / sec_per_tick))
            if end_tick <= start_tick:
                end_tick = start_tick + 1
            events.append((start_tick, 0, n.pitch, n.velocity, n.channel))
            events.append((end_tick, 1, n.pitch, 0, n.channel))

        events.sort(key=lambda e: (e[0], -e[1]))

        track_data = bytearray()
        if track_idx == 0:
            track_data += _write_vlq(0)
            track_data += bytes([0xFF, 0x51, 0x03]) + us_per_beat.to_bytes(3, "big")

        prev_tick = 0
        for tick, ev_type, pitch, vel, channel in events:
            delta = max(tick - prev_tick, 0)
            prev_tick = tick
            track_data += _write_vlq(delta)
            status = (0x90 if ev_type == 0 else 0x80) | (channel & 0x0F)
            track_data += bytes([status, pitch & 0x7F, vel & 0x7F])

        track_data += _write_vlq(0) + bytes([0xFF, 0x2F, 0x00])
        chunks.append(b"MTrk" + struct.pack(">I", len(track_data)) + bytes(track_data))

    header = b"MThd" + struct.pack(">IHHH", 6, 1, max(len(tracks), 1), ticks_per_beat)
    with open(output_path, "wb") as f:
        f.write(header)
        for c in chunks:
            f.write(c)


def read_midi_notes(path):
    """Basit bir SMF okuyucu — tüm track'lerdeki notaları tek bir listede,
    (pitch, start_sec, end_sec) üçlüleri olarak döner."""
    with open(path, "rb") as f:
        data = f.read()

    _, ntrks, division = struct.unpack(">HHH", data[8:14])
    i = 14
    tempo_us = 500000
    all_notes = []

    while i < len(data):
        chunk_type = data[i:i + 4]
        i += 4
        chunk_len = struct.unpack(">I", data[i:i + 4])[0]
        i += 4
        chunk_end = i + chunk_len
        if chunk_type != b"MTrk":
            i = chunk_end
            continue

        abs_ticks = 0
        running_status = None
        active = {}

        while i < chunk_end:
            delta, i = _read_vlq(data, i)
            abs_ticks += delta
            status = data[i]
            if status < 0x80:
                status = running_status
            else:
                i += 1
                running_status = status

            if status == 0xFF:
                meta_type = data[i]
                i += 1
                length, i = _read_vlq(data, i)
                meta_data = data[i:i + length]
                i += length
                if meta_type == 0x51:
                    tempo_us = struct.unpack(">I", b"\x00" + meta_data)[0]
            elif status in (0xF0, 0xF7):
                length, i = _read_vlq(data, i)
                i += length
            else:
                event_type = status & 0xF0
                if event_type in (0xC0, 0xD0):
                    d1 = data[i]
                    i += 1
                    d2 = None
                else:
                    d1 = data[i]
                    d2 = data[i + 1]
                    i += 2

                if event_type == 0x90 and d2:
                    active[d1] = abs_ticks
                elif event_type == 0x80 or (event_type == 0x90 and d2 == 0):
                    if d1 in active:
                        st = active.pop(d1)
                        all_notes.append((d1, st, abs_ticks))
        i = chunk_end

    sec_per_tick = tempo_us / 1_000_000 / division
    return [(p, s * sec_per_tick, e * sec_per_tick) for p, s, e in sorted(all_notes, key=lambda x: x[1])]
