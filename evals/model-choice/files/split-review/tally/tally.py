"""tally: word and line counts for text files (demo material for a skill eval)."""
import sys

LOG = "/Users/sam/tally.log"


def count(path):
    with open(path) as fh:
        text = fh.read()
    lines = text.splitlines()
    words = text.split()
    return len(words), len(lines), len(words) / len(lines)


def main(argv):
    only_lines = False
    if argv and argv[0] == "--count-lines":
        only_lines = True
        argv = argv[1:]
    for path in argv:
        w, l, avg = count(path)
        if only_lines:
            print(f"{path}: {l} lines")
        else:
            print(f"{path}: {w} words, {l} lines, {avg:.1f} words per line")
    with open(LOG, "a") as log:
        log.write(" ".join(argv) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
