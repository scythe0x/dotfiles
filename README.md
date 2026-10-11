# dotfiles

- **zsh**: prompt, алиасы, path и интеграции инструментов.
- **brew**: пакеты и приложения в `Brewfile`.
- **cursor**: настройки, горячие клавиши и список расширений.
- **vscode**: настройки и горячие клавиши.
- **iterm2**: профили, цвета, шрифты и горячие клавиши.
- **codex**: основной конфиг без токена.

## one-line install

из каталога скачанного репозитория:

```sh
bash ./install.sh
```

скрипт устанавливает homebrew, chezmoi и пакеты из `Brewfile`, затем применяет конфиги из этого репозитория.

> [!WARNING]
> перед запуском закрой редакторы и iterm2.

## расширения cursor

добавь команду `cursor` в path через command palette, затем:

```sh
xargs -n 1 cursor --install-extension < "$(chezmoi source-path)/metadata/cursor-extensions.txt"
```

## сохранить конфиги с mac

```sh
chezmoi add --secrets=error ~/.zshrc ~/.zprofile
cd "$(chezmoi source-path)"
brew bundle dump --file=Brewfile --force --formula --cask --tap --no-describe --no-restart
cursor --list-extensions > metadata/cursor-extensions.txt
git diff
# убери ненужные пакеты из brewfile перед коммитом
git add .
git commit -m "update dotfiles"
git push
```

конфиг codex редактируй через `chezmoi edit ~/.codex/config.toml`, чтобы сохранить шаблон без токена.

## добавить новый конфиг

подставь путь к существующему конфигу без токенов и паролей:

```sh
chezmoi add --secrets=error ~/.config/example/config.toml
cd "$(chezmoi source-path)"
git add .
git diff --cached
git commit -m "add example config"
git push
```

на другом компьютере `chezmoi update` загрузит изменения и восстановит файл на том же месте.
