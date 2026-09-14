# GTM JatengGayeng Bot

## Purpose

Telegram bot untuk membantu user melakukan input data event GTM.

## User Flow

1. User menjalankan /start
2. User memilih Branch (pilihan)
3. User memilih  (pilihan)
4. User memasukkan nama event (ketik manual, jangan sampai kosong)
5. User memilih Tag Lokasi (dichat telegram pilih lokasi atau minta lokasi, lalu disimpan sebagai latitude, dan longitude)
6. Bot menampilkan konfirmasi (berisi ringkasan data yang akan dimasukkan + muncul tombol submit)
7. User melakukan Submit
8. Sistem menyimpan data

## Fields

- Branch
- WOK
- Event Name
- Location Tag

## Unknowns

- Sumber data Branch belum ditentukan
- Sumber data WOK belum ditentukan
- Sumber Tag Lokasi belum ditentukan
- Destination data setelah Submit belum ditentukan
- Authentication/authorization belum ditentukan

## General Rules

1. Do not invent requirements.
2. Do not invent database schema when the schema is not specified.
3. Do not invent API endpoints.
4. Do not invent environment variables.
5. Do not assume external services exist.
6. If information is missing, explicitly mark it as an assumption.
7. Prefer asking for clarification over making critical assumptions.
8. Never modify unrelated files.
9. Keep changes small and focused.
10. Do not rewrite working code without a reason.

## Development Workflow

Before implementing a feature:

1. Inspect the existing project.
2. Read requirements.
3. Identify relevant files.
4. Explain the proposed implementation.
5. Identify assumptions.
6. Wait for approval if the change is architectural or destructive.

After implementation:

1. Run tests.
2. Run lint/type checks if available.
3. Review the diff.
4. Report what changed.
5. Report remaining risks.