# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-09-16

### Added

- **BREAKING** 移除人审闸门，改为纯观测（主人定调：防御体系不应该有人工审核） — [`d4af374`](https://github.com/jonah791/dsh-prompt-defense/commit/d4af374745eac888eb97d88113beed6af0f1cce1)
- init: dsh-prompt-defense v0.1.0 — L1 来源标记 / L2 注入检测 / L3 危险动作人审 / L4 审计侧车；9 条尸体测试全绿（含 2026-09-15 现场漏报回归夹具） — [`c1cbb62`](https://github.com/jonah791/dsh-prompt-defense/commit/c1cbb62464d792ba171ebbdb69e73a20d39cabea)

### Fixed

- 三处现场误报（上线首夜自锁）——exfil-target URL 过宽 / 只读工具被误判高危 / 凭据路径检查作用于正文 — [`0db56ec`](https://github.com/jonah791/dsh-prompt-defense/commit/0db56ec17660c04179b3853508e4d710590e12c7)

### Changed

- 同步移除人审后的语义（README 四层表/配置/落盘/测试/设计要点；A3 判据废止并重述为 A3'） — [`c02243c`](https://github.com/jonah791/dsh-prompt-defense/commit/c02243ce6fdca4f9a35e237794f43288b4193b1c)
- 补 LICENSE 文件（GitHub 需文件才识别 MIT，package.json 字段不足） — [`b279b28`](https://github.com/jonah791/dsh-prompt-defense/commit/b279b286564fd84da68ab94c1a6926904db0c83c)
