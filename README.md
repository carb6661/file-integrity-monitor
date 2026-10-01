# File Integrity Monitor

一个零依赖的 Python 命令行工具：为指定目录建立 SHA-256 文件指纹清单，并在之后的校验中识别新增、删除和被修改的文件。

> 仅用于你拥有或明确获授权检查的目录。本项目是防御性安全与密码学基础的教学示例，不包含入侵、规避或破坏功能。

## 功能

- 递归扫描普通文件，不跟随符号链接
- 以分块方式计算 SHA-256，适合较大文件
- 输出可审阅、可版本管理的 JSON 清单
- 精确区分新增、删除、修改三种变化
- 不依赖第三方库，支持 Python 3.9+

## 快速开始

```bash
git clone https://github.com/carb6661/file-integrity-monitor.git
cd file-integrity-monitor
python fim.py snapshot ./demo -o ./baseline.json
python fim.py verify ./demo -m ./baseline.json
```

也可以安装为命令：

```bash
python -m pip install .
fim snapshot ./demo -o ./baseline.json
fim verify ./demo -m ./baseline.json
```

当目录未改变时，`verify` 返回退出码 `0`。若发现变化，会打印分类结果并返回 `1`，便于接入 CI 或定时任务。

## 示例

```text
[新增] uploads/report.pdf
[删除] config/legacy.ini
[修改] app/settings.json
完整性检查失败：新增 1，删除 1，修改 1。
```

## 运行测试

```bash
python -m unittest discover -s tests -v
```

## 项目结构

```text
.
├── fim.py              # 命令行与完整性校验核心逻辑
├── tests/test_fim.py   # 单元测试
├── pyproject.toml      # 安装与项目元数据
└── README.md
```

## 学习要点

1. **完整性与机密性不同**：哈希能帮助发现内容变化，但不会加密文件。
2. **基线必须可信**：若攻击者能同时替换文件和清单，校验就没有意义；生产环境应保护或签名清单。
3. **哈希并非所有威胁的答案**：本工具只报告内容变化，不能判断变化是否恶意。
4. **自动化响应要谨慎**：检测到变化后应先调查、保留证据并执行既定流程，避免盲目删除文件。

## 许可证

[MIT](LICENSE)
