# Machine audit — UNVERIFIED, MUST BE RE-RUN ON THE MAC

> **Status: provisional.** Every value below was read off a *screenshot* of System Information,
> not detected on the machine. The session that wrote this ran in a Linux x86_64 container with no
> access to the Mac. Re-run the commands in §2 and replace this file with real output before any
> rendering decision depends on it.

## 1. Provisional values (from a System Information screenshot, 2026-09-10)

| Field | Value |
|---|---|
| Model Name | MacBook Air |
| Model Identifier | Mac14,2 |
| Model Number | MC7X4B/A |
| Chip | Apple M2 |
| Total cores | 8 (4 performance, 4 efficiency) |
| Memory | 16 GB unified |
| System Firmware | 18000.161.10 |
| Activation Lock | Enabled |

Not visible in the screenshot and therefore unknown: **GPU core count** (M2 Air ships in 8-core and
10-core GPU variants — this materially affects the rendering budget), macOS version, Xcode version,
free disk space, Metal feature set, and whether UE 5.8 is installed at all.

Mac14,2 is the fanless M2 MacBook Air. Sustained GPU load will thermally throttle; benchmark warm.

## 2. Commands to run, replacing this file with the output

```bash
system_profiler SPHardwareDataType
system_profiler SPDisplaysDataType     # GPU core count lives here
sw_vers
uname -m                               # expect arm64; x86_64 means Rosetta
xcodebuild -version
xcode-select -p
df -h /
```

Then locate Unreal rather than assuming a path:

```bash
ls -d "/Users/Shared/Epic Games/"* 2>/dev/null
ls -d /Applications/UE_* /Applications/Epic* 2>/dev/null
mdfind -name "UnrealEditor" 2>/dev/null | head
```

Record, per the brief §3: UE version and install path, Launcher binary vs source build, whether
`UnrealEditor-Cmd` is callable, whether the Python Editor Script Plugin is available, which
required plugins are already enabled, and anything unexpectedly running under Rosetta.

## 3. Decisions that depend on these values

- **GPU core count (8 vs 10)** — sets the realistic foliage density and shadow distance budget.
- **macOS + Metal feature set** — whether hardware ray tracing is available at all; assume Lumen
  software tracing until proven otherwise.
- **Free disk** — a UE 5.8 install plus DDC plus this project's source assets needs well over
  100 GB; check before importing.
- **Xcode first-launch state** — required for C++ compilation; a licence prompt or missing
  components will block builds and may need GUI interaction.
