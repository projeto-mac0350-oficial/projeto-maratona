# Code metrics — `backend`

_Generated 2026-06-28 14:59 UTC_ · Python files analysed: 1_

Collected with **radon** (complexity & maintainability) and **pylint** (quality score).

## Cyclomatic complexity — `radon cc -s -a`
Lower is simpler. Each block is graded A (best) to F; the average is at the end.
```
backend/app.py
    F 97:0 login - B (8)
    F 73:0 register - B (7)
    F 21:0 get_db - A (1)
    F 28:0 init_db - A (1)
    F 43:0 login_required - A (1)
    F 59:0 index - A (1)
    F 68:0 health - A (1)
    F 120:0 logout - A (1)
    F 127:0 me - A (1)

9 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.4444444444444446)
```

## Maintainability index — `radon mi -s`
0-100, higher is more maintainable. A = very maintainable, C = hard to maintain.
```
backend/app.py - A (57.49)
```

## Raw metrics — `radon raw -s`
Lines of code (LOC), logical (LLOC) and source (SLOC) lines, comments, blanks.
```
backend/app.py
    LOC: 136
    LLOC: 75
    SLOC: 87
    Comments: 8
    Single comments: 12
    Multi: 0
    Blank: 37
    - Comment Stats
        (C % L): 6%
        (C % S): 9%
        (C + M % L): 6%
** Total **
    LOC: 136
    LLOC: 75
    SLOC: 87
    Comments: 8
    Single comments: 12
    Multi: 0
    Blank: 37
    - Comment Stats
        (C % L): 6%
        (C % S): 9%
        (C + M % L): 6%
```

## Halstead complexity — `radon hal`
Volume / difficulty / effort derived from operators and operands.
```
backend/app.py:
    h1: 5
    h2: 29
    N1: 18
    N2: 31
    vocabulary: 34
    length: 49
    calculated_length: 152.49108933313642
    volume: 249.28567922126666
    difficulty: 2.6724137931034484
    effort: 666.1944875740747
    time: 37.010804865226376
    bugs: 0.08309522640708888
```

## Quality score — `pylint`
Static analysis with a final score "rated at X/10".
```
************* Module app
backend/app.py:1:0: C0114: Missing module docstring (missing-module-docstring)
backend/app.py:68:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:73:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:97:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:120:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:127:0: C0116: Missing function or method docstring (missing-function-docstring)

------------------------------------------------------------------
Your code has been rated at 9.05/10 (previous run: 9.05/10, +0.00)

```
