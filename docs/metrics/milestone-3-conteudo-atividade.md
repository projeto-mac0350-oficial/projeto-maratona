# Code metrics — `backend`

_Generated 2026-07-30 15:24 UTC_ · Python files analysed: 6_

Collected with **radon** (complexity & maintainability) and **pylint** (quality score).

## Cyclomatic complexity — `radon cc -s -a`
Lower is simpler. Each block is graded A (best) to F; the average is at the end.
```
backend/app.py
    F 286:0 login - B (8)
    F 365:0 set_progress - B (8)
    F 262:0 register - B (7)
    F 430:0 get_topic - B (6)
    F 166:0 seed_content - A (4)
    F 324:0 get_activity - A (4)
    F 396:0 _serialize_item - A (4)
    F 29:0 init_db - A (3)
    F 234:0 compute_streak - A (2)
    F 344:0 get_progress - A (2)
    F 420:0 list_topics - A (2)
    F 22:0 get_db - A (1)
    F 212:0 login_required - A (1)
    F 224:0 record_login_day - A (1)
    F 248:0 index - A (1)
    F 257:0 health - A (1)
    F 310:0 logout - A (1)
    F 317:0 me - A (1)
backend/tests/test_progress.py
    F 36:0 test_post_progress_saves_and_is_returned - A (4)
    F 58:0 test_post_progress_upserts_in_place - A (4)
    F 27:0 test_progress_starts_empty - A (3)
    F 51:0 test_post_progress_requires_item_key_and_kind - A (3)
    F 78:0 test_progress_is_per_user - A (3)
    F 16:0 test_get_progress_requires_authentication - A (2)
    F 20:0 test_post_progress_requires_authentication - A (2)
    F 69:0 test_missing_done_defaults_to_false - A (2)
backend/tests/test_auth.py
    F 19:0 test_register_requires_username_and_password - A (4)
    F 75:0 test_me_returns_logged_in_user - A (4)
    F 83:0 test_logout_clears_the_session - A (4)
    F 4:0 test_health_ok - A (3)
    F 13:0 test_register_creates_user - A (3)
    F 31:0 test_password_is_not_stored_in_plaintext - A (3)
    F 46:0 test_login_with_valid_credentials - A (3)
    F 25:0 test_register_rejects_duplicate_username - A (2)
    F 53:0 test_login_with_wrong_password_is_unauthorized - A (2)
    F 59:0 test_login_unknown_user_is_unauthorized - A (2)
    F 64:0 test_login_requires_fields - A (2)
    F 71:0 test_me_requires_authentication - A (2)
backend/tests/test_content.py
    F 12:0 test_list_topics_includes_busca_binaria - B (8)
    F 33:0 test_get_topic_returns_references_and_problems - B (8)
    F 47:0 test_get_topic_problem_has_links_and_label - B (7)
    F 23:0 test_list_topics_does_not_leak_items - A (5)
    F 56:0 test_get_topic_reference_label_is_the_title - A (5)
    F 75:0 test_problems_expose_their_difficulty - A (5)
    F 83:0 test_references_have_no_difficulty - A (4)
    F 63:0 test_get_topic_items_keep_authoring_order - A (2)
    F 68:0 test_get_unknown_topic_is_404 - A (2)
    F 92:0 test_content_item_keys_match_progress_storage - A (2)
backend/tests/conftest.py
    F 18:0 client - A (1)
    F 31:0 auth_client - A (1)
backend/tests/test_activity.py
    F 77:0 test_activity_self_records_and_shape - A (3)
    F 85:0 test_streak_counts_consecutive_days - A (3)
    F 98:0 test_days_lists_only_current_month - A (3)
    F 18:0 seed_days - A (2)
    F 35:0 recorded_days - A (2)
    F 48:0 test_activity_requires_authentication - A (2)
    F 55:0 test_login_records_today - A (2)
    F 61:0 test_me_records_today - A (2)
    F 67:0 test_duplicate_recording_is_idempotent - A (2)
    F 92:0 test_gap_resets_streak - A (2)
    F 109:0 test_activity_is_per_user - A (2)
    F 127:0 test_compute_streak_empty - A (2)
    F 131:0 test_compute_streak_spans_month_boundary - A (2)
    F 14:0 iso_days_ago - A (1)
    F 30:0 clear_days - A (1)

65 blocks (classes, functions, methods) analyzed.
Average complexity: A (3.0)
```

## Maintainability index — `radon mi -s`
0-100, higher is more maintainable. A = very maintainable, C = hard to maintain.
```
backend/app.py - A (42.83)
backend/tests/test_progress.py - A (67.03)
backend/tests/test_auth.py - A (53.35)
backend/tests/test_content.py - A (61.32)
backend/tests/conftest.py - A (94.14)
backend/tests/test_activity.py - A (63.95)
```

## Raw metrics — `radon raw -s`
Lines of code (LOC), logical (LLOC) and source (SLOC) lines, comments, blanks.
```
backend/app.py
    LOC: 460
    LLOC: 170
    SLOC: 357
    Comments: 28
    Single comments: 39
    Multi: 2
    Blank: 62
    - Comment Stats
        (C % L): 6%
        (C % S): 8%
        (C + M % L): 7%
backend/tests/test_progress.py
    LOC: 91
    LLOC: 52
    SLOC: 52
    Comments: 10
    Single comments: 9
    Multi: 0
    Blank: 30
    - Comment Stats
        (C % L): 11%
        (C % S): 19%
        (C + M % L): 11%
backend/tests/test_auth.py
    LOC: 87
    LLOC: 66
    SLOC: 52
    Comments: 3
    Single comments: 4
    Multi: 0
    Blank: 31
    - Comment Stats
        (C % L): 3%
        (C % S): 6%
        (C + M % L): 3%
backend/tests/test_content.py
    LOC: 107
    LLOC: 61
    SLOC: 64
    Comments: 7
    Single comments: 5
    Multi: 7
    Blank: 31
    - Comment Stats
        (C % L): 7%
        (C % S): 11%
        (C + M % L): 13%
backend/tests/conftest.py
    LOC: 35
    LLOC: 23
    SLOC: 18
    Comments: 4
    Single comments: 5
    Multi: 4
    Blank: 8
    - Comment Stats
        (C % L): 11%
        (C % S): 22%
        (C + M % L): 23%
backend/tests/test_activity.py
    LOC: 133
    LLOC: 72
    SLOC: 76
    Comments: 9
    Single comments: 7
    Multi: 6
    Blank: 44
    - Comment Stats
        (C % L): 7%
        (C % S): 12%
        (C + M % L): 11%
** Total **
    LOC: 913
    LLOC: 444
    SLOC: 619
    Comments: 61
    Single comments: 69
    Multi: 19
    Blank: 206
    - Comment Stats
        (C % L): 7%
        (C % S): 10%
        (C + M % L): 9%
```

## Halstead complexity — `radon hal`
Volume / difficulty / effort derived from operators and operands.
```
backend/app.py:
    h1: 9
    h2: 59
    N1: 36
    N2: 65
    vocabulary: 68
    length: 101
    calculated_length: 375.60526492532944
    volume: 614.8337469662844
    difficulty: 4.9576271186440675
    effort: 3048.116457417596
    time: 169.33980318986644
    bugs: 0.20494458232209478
backend/tests/test_progress.py:
    h1: 3
    h2: 28
    N1: 15
    N2: 30
    vocabulary: 31
    length: 45
    calculated_length: 139.36082531977635
    volume: 222.9388339674094
    difficulty: 1.6071428571428572
    effort: 358.29455459047944
    time: 19.905253032804413
    bugs: 0.07431294465580314
backend/tests/test_auth.py:
    h1: 4
    h2: 36
    N1: 22
    N2: 44
    vocabulary: 40
    length: 66
    calculated_length: 194.11730005192322
    volume: 351.24725426256595
    difficulty: 2.4444444444444446
    effort: 858.6043993084946
    time: 47.70024440602748
    bugs: 0.11708241808752198
backend/tests/test_content.py:
    h1: 5
    h2: 51
    N1: 26
    N2: 52
    vocabulary: 56
    length: 78
    calculated_length: 300.9033329149831
    volume: 452.97368392049316
    difficulty: 2.549019607843137
    effort: 1154.6388021502767
    time: 64.14660011945982
    bugs: 0.15099122797349773
backend/tests/conftest.py:
    h1: 1
    h2: 2
    N1: 1
    N2: 2
    vocabulary: 3
    length: 3
    calculated_length: 2.0
    volume: 4.754887502163469
    difficulty: 0.5
    effort: 2.3774437510817346
    time: 0.1320802083934297
    bugs: 0.0015849625007211565
backend/tests/test_activity.py:
    h1: 4
    h2: 30
    N1: 15
    N2: 30
    vocabulary: 34
    length: 45
    calculated_length: 155.20671786825557
    volume: 228.9358278562653
    difficulty: 2.0
    effort: 457.8716557125306
    time: 25.4373142062517
    bugs: 0.0763119426187551
```

## Quality score — `pylint`
Static analysis with a final score "rated at X/10".
```
************* Module app
backend/app.py:1:0: C0114: Missing module docstring (missing-module-docstring)
backend/app.py:257:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:262:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:286:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:310:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/app.py:317:0: C0116: Missing function or method docstring (missing-function-docstring)
************* Module conftest
backend/tests/conftest.py:14:0: C0413: Import "import app as flask_app" should be placed at the top of the module (wrong-import-position)
backend/tests/conftest.py:31:16: W0621: Redefining name 'client' from outer scope (line 18) (redefined-outer-name)
************* Module test_activity
backend/tests/test_activity.py:14:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:30:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:35:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:48:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:55:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:61:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:67:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:77:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:85:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:92:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:98:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:109:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:109:30: W0613: Unused argument 'auth_client' (unused-argument)
backend/tests/test_activity.py:127:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_activity.py:131:0: C0116: Missing function or method docstring (missing-function-docstring)
************* Module test_auth
backend/tests/test_auth.py:4:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:13:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:19:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:25:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:31:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:33:4: C0415: Import outside toplevel (app) (import-outside-toplevel)
backend/tests/test_auth.py:46:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:53:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:59:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:64:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:71:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:75:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_auth.py:83:0: C0116: Missing function or method docstring (missing-function-docstring)
************* Module test_content
backend/tests/test_content.py:12:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_content.py:33:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_content.py:47:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_content.py:56:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_content.py:63:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_content.py:68:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_content.py:75:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_content.py:83:0: C0116: Missing function or method docstring (missing-function-docstring)
************* Module test_progress
backend/tests/test_progress.py:16:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_progress.py:20:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_progress.py:27:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_progress.py:36:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_progress.py:51:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_progress.py:58:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_progress.py:69:0: C0116: Missing function or method docstring (missing-function-docstring)
backend/tests/test_progress.py:78:0: C0116: Missing function or method docstring (missing-function-docstring)

-----------------------------------
Your code has been rated at 8.56/10

```
