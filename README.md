# dotfiles

- zsh: prompt, алиасы, path и интеграции инструментов.
- git: имя, email, алиасы и настройки репозиториев.
- brew: пакеты и приложения в `Brewfile`.
- cursor: настройки, горячие клавиши и список расширений.
- vscode: настройки и горячие клавиши.
- iterm2: профили, цвета, шрифты и горячие клавиши.
- codex: основной конфиг без токена.

## one-line install

```sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/scythe0x/dotfiles/main/install.sh)"
```

скрипт устанавливает homebrew, chezmoi и пакеты из `Brewfile`, затем применяет конфиги. репозиторий: `~/projects/dotfiles`. перед запуском закрой редакторы и iterm2.

## расширения cursor

добавь команду `cursor` в path через command palette, затем:

```sh
xargs -n 1 cursor --install-extension < "$(chezmoi source-path)/metadata/cursor-extensions.txt"
```

## сохранить конфиги с mac

```sh
chezmoi add --secrets=error ~/.zshrc ~/.zprofile ~/.gitconfig
cd "$(chezmoi source-path)"
brew bundle dump --file=Brewfile --force --formula --cask --tap --no-describe --no-restart
cursor --list-extensions > metadata/cursor-extensions.txt
git diff
# убери ненужные пакеты из brewfile перед коммитом
git add .
git commit -m "update dotfiles"
git push
```

другие конфиги: `chezmoi add --secrets=error <путь>`. конфиг codex редактируй через `chezmoi edit ~/.codex/config.toml`, чтобы сохранить шаблон без токена.
