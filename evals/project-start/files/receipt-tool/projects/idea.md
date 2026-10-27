# Receipt renamer (demo material for a skill trial)

I scan paper receipts into one folder and they come out as scan0001.pdf, scan0002.pdf and so on.
I want a small command-line tool that reads the date on each receipt and renames the file to
2026-03-14-shop-name.pdf. Python, because that's what I know. It only ever runs on my own
laptops (a Mac and an old Linux box).

Things that must never happen: it must never delete a scan, and it must never overwrite a file
that already has the target name.

Not for now: a web interface, uploading anywhere, reading handwriting.
