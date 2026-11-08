# Finding obfuscated names in a new Facebook Lite version

The extensions name obfuscated classes and members (`X.0hd`, field `A2e`, method `ADt`, ...). These change
with every Facebook Lite release. These scripts find the new names by comparing the code of the version the
extensions were written for with the new one. `mapping-530-to-536.txt` is the result of the last update and
lists every name the extensions use.

Requirements: python3, a JDK, Maven (the first `disassemble.sh` run fetches baksmali from Google's Maven
repository), and the Superpack decoder from [../superpack](../superpack).

## Steps

1. **Get both APKs and decode both stores** with `../superpack/decode.sh`.

2. **Disassemble both versions** into smali, then summarise each once to speed up the next steps:
   ```sh
   ./disassemble.sh fb-old.apk out/dex-old out/smali-old
   ./disassemble.sh fb-new.apk out/dex-new out/smali-new
   python3 index.py out/smali-old out/old.pkl
   python3 index.py out/smali-new out/new.pkl
   ```

3. **Match classes.** Compares each old class's shape (fields, method signatures and sizes, strings, API
   calls) with every new class. A winner close to 1.00 far ahead of the rest is reliable. Tiny classes can tie
   (`X/1In` scored 1.00 against three classes); settle those from a signature that uses them, for example the
   return type of `X/0ei.A03`.
   ```sh
   python3 match.py out/old.pkl out/new.pkl X/1DY X/0eF X/0gp
   # LX/1DY; LX/1E8;=0.93  LX/1C8;=0.31  ...
   ```

4. **Map fields and methods** of each class pair. Obfuscated names are handed out in order, so one added
   field renames every field after it. `members.py` aligns the fields by type, and methods by signature and
   code:
   ```sh
   python3 members.py out/old.pkl out/new.pkl X/0zb X/12u A07 A08 m:AQS
   ```
   `pdiff.sh` shows one class's code differences with class names normalised. Empty output means only the
   class name changed.

5. **Confirm from usage.** Type alignment cannot place a field inside a long run of the same type (`X/0hd`
   has 60 booleans in a row). `crossref.py` lines up the code of matched methods and counts which new name
   appears where each old name did. It also discovers more class pairs as it goes:
   ```sh
   python3 crossref.py out/smali-old out/smali-new "X/1DY=X/1E8,X/0gp=X/0hd,X/0zb=X/12u" out/map.json 2
   python3 query.py out/map.json X/0z8 'X/0gp->A2c'
   ```
   Few or split votes (`A2C (3), A2e (2)`) mean you need another source of evidence. For 536 this was the
   one-field restore methods `X/0hd.A0D`..`A0V`: each restores one field from a map key, and comparing the
   keys and fields in both versions showed exactly where the new boolean was inserted. The video listener's
   method names came from the dispatch switch in `X/3jN` / `X/3mG`, whose cases call the same methods in the
   same order.

6. **Write the mapping** in the format of `mapping-530-to-536.txt` and check that every field keeps its type:
   ```sh
   python3 check-fields.py out/old.pkl out/new.pkl mapping-old-to-new.txt
   ```

7. **Update the extensions**: the `X.$xxx` replacement classes and stubs (rename the files too), the
   `Class.forName("X.xxx")` and `getDeclaredField("Axx")` strings, `COMPATIBILITY_FACEBOOK_LITE_<version>`
   in `patches/.../shared/Constants.kt`, and the loader table in `OriginalClass` / `OriginalRasterizer`
   (`X/09V` is in the primary dex). Then check that each stub's kind (interface, abstract or final) matches
   the real class.
