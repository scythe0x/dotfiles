# dotfiles

Личные настройки macOS, сохранённые в Git и управляемые [chezmoi](https://www.chezmoi.io/).
Репозиторий приватный. Токены и пароли в него не входят.

## Что сохранено

- Zsh, Bash, Git, IdeaVim, Yarn, Taskwarrior и Nuxt.
- Ghostty, Hyper, iTerm2 и горячие клавиши Warp.
- Настройки и горячие клавиши VS Code и Cursor; списки расширений — в `metadata/`.
- Neofetch, shell-интеграции Fish и uv.
- Codex: конфиг, общие инструкции `AGENTS.md` и локальные skills.
- OpenCode и Cursor MCP: настройки без секретных ключей.
- `Brewfile`: снимок установленных через Homebrew пакетов, а также обнаруженных расширений, npm- и Go-пакетов.
- `metadata/applications.txt`: список приложений для ручного восстановления; `runtime-versions.txt` — версии среды на момент сбора.

Абсолютные пути `/Users/akv` в текстовых настройках подставляются из домашнего каталога назначения.
Остальные настройки сохранены как есть. В Zsh исправлена опечатка `compinits`, добавлены проверки наличия fzf, zoxide и completion OpenClaw.

## Восстановление на новом Mac

Установить Homebrew по [официальной инструкции](https://brew.sh/), затем:

```sh
brew install chezmoi gh
gh auth login
gh auth setup-git
chezmoi init https://github.com/scythe0x/dotfiles.git
chezmoi diff
chezmoi apply
```

Закрыть iTerm2 перед применением его plist: запущенное приложение может перезаписать настройки при выходе.
Также закрыть редакторы, если они меняют настройки во время восстановления.

Установка программ выполняется отдельно, после просмотра `Brewfile`:

```sh
chezmoi cd
brew bundle --file=Brewfile
```

Это снимок текущей установки, а не универсальный установщик. Некоторые пакеты могут устареть;
Homebrew может запросить доверие к сторонним taps. Brewfile содержит настройки запуска существующих сервисов.
Пакеты Go/npm требуют соответствующих сред; NVM, Bun, Python из python.org, приложения вне Homebrew
и шрифт GeistMono устанавливаются отдельно. Версии NVM/Node указаны в `metadata/runtime-versions.txt`.

Расширения Cursor можно восстановить после установки его CLI:

```sh
while IFS= read -r extension; do
    cursor --install-extension "$extension" || break
done < metadata/cursor-extensions.txt
```

Часть настроек редакторов ссылается на конкретные версии расширений и SDK. После установки новых версий
эти пути может потребоваться обновить. Completion OpenClaw создаётся самим OpenClaw; без него shell запускается.

## Секреты

В трёх шаблонах ключи читаются только из существующего файла на компьютере назначения:

| Файл                             | Локальное поле                                                 |
| -------------------------------- | -------------------------------------------------------------- |
| `~/.codex/config.toml`           | `mcp_servers.tmm_-tradermakemoney-.http_headers.Authorization` |
| `~/.config/opencode/config.json` | `provider.customapi.options.apiKey`                            |
| `~/.cursor/mcp.json`             | Аргумент после `--key` у `duckduckgo-mcp-server`               |

На новом компьютере поля будут пустыми: нужно вручную добавить ключи в установленные файлы.
Последующие `chezmoi apply` сохранят эти значения. Если существующий файл не разбирается как TOML/JSON,
рендеринг остановится с ошибкой, чтобы не потерять его ключ.

**Не выполнять `chezmoi add` или `chezmoi re-add` для этих трёх файлов:** это может заменить шаблон копией с токеном.
Несекретные настройки в них менять через `chezmoi edit`, ключи — только в установленном файле.
`chezmoi diff` может показывать локальные секреты; его вывод не публиковать.

Не сохранены авторизации, SSH-ключи, базы данных, история, сессии, кеши, облачные credentials,
данные торговых приложений и внутренние базы Raycast. Настройки расширений/сниппетов Raycast требуют
отдельного экспорта через Raycast Settings → Advanced → Export; plist не заменяет этот экспорт.
Dotfiles дополняют полноценный бэкап, например Time Machine.

## Повседневное использование

На текущем компьютере chezmoi уже настроен на `~/projects/dotfiles`.

Добавить новый проверенный конфиг:

```sh
chezmoi add --secrets=error ~/.config/example/config.toml
```

Сохранить изменения обычного конфига, отредактированного приложением:

```sh
chezmoi add --secrets=error ~/.gitconfig
chezmoi cd
git diff
git add .
git commit -m "Update Git settings"
git push
```

Для шаблонов с переносимыми путями предпочтительнее `chezmoi edit ~/.zshrc`, затем `chezmoi diff` и `chezmoi apply`.
Прямое повторное добавление файла заменяет шаблон обычной копией.
GitHub получает изменения только после `git push`; автоматического бэкапа нет.

## Проверка

Нужны chezmoi, Python 3.11+, Bash и Zsh:

```sh
python3 -m unittest discover -s tests -v
chezmoi verify
git diff --check
```

Тесты применяют весь набор в отдельный временный каталог, проверяют повторное применение,
сохранение локальных ключей, отсутствие секретов при чистом восстановлении и поведение при повреждённом конфиге.
Программы и их сервисы при тестировании не устанавливаются и не запускаются.
