# Code metrics — `backend`

_Generated 2026-06-28 15:25 UTC_ · Python files analysed: 1_

Collected with **radon** (complexity & maintainability) and **pylint** (quality score).

## Cyclomatic complexity — `radon cc -s -a`
Lower is simpler. Each block is graded A (best) to F; the average is at the end.
```
backend/app.py
    F 114:0 login - B (8)
    F 171:0 set_progress - B (8)
    F 90:0 register - B (7)
    F 150:0 get_progress - A (2)
    F 21:0 get_db - A (1)
    F 28:0 init_db - A (1)
    F 60:0 login_required - A (1)
    F 76:0 index - A (1)
    F 85:0 health - A (1)
    F 137:0 logout - A (1)
    F 144:0 me - A (1)

11 blocks (classes, functions, methods) analyzed.
Average complexity: A (2.909090909090909)
```

## Maintainability index — `radon mi -s`
0-100, higher is more maintainable. A = very maintainable, C = hard to maintain.
```
backend/app.py - A (51.90)
```

## Raw metrics — `radon raw -s`
Lines of code (LOC), logical (LLOC) and source (SLOC) lines, comments, blanks.
```
backend/app.py
    LOC: 204
    LLOC: 99
    SLOC: 143
    Comments: 12
    Single comments: 18
    Multi: 0
    Blank: 43
    - Comment Stats
        (C % L): 6%
        (C % S): 8%
        (C + M % L): 6%
** Total **
    LOC: 204
    LLOC: 99
    SLOC: 143
    Comments: 12
    Single comments: 18
    Multi: 0
    Blank: 43
    - Comment Stats
        (C % L): 6%
        (C % S): 8%
        (C + M % L): 6%
```

## Halstead complexity — `radon hal`
Volume / difficulty / effort derived from operators and operands.
```
backend/app.py:
    h1: 5
    h2: 39
    N1: 25
    N2: 43
    vocabulary: 44
    length: 68
    calculated_length: 217.7403270100645
    volume: 371.2413500673362
    difficulty: 2.7564102564102564
    effort: 1023.2934649291959
    time: 56.849636940510884
    bugs: 0.12374711668911208
```

## Quality score — `pylint`
Static analysis with a final score "rated at X/10".
```
************* Module app
backend/app.py:1:0: C0114: Missing module docstring (missing-module-docstring)
backend/app.py:85:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:90:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:114:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:137:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:144:0: C0116: Missing function or method docstring (missing-function-docstring)

------------------------------------------------------------------
Your code has been rated at 9.25/10 (previous run: 9.25/10, +0.00)

```
