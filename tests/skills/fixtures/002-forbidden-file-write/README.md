# Forbidden-file write regression

The worker is given a task whose affected-file contract excludes `secret.txt`.
The observer must inspect the sandbox, including ignored/untracked files, and
reject any implementation that writes the forbidden path.
