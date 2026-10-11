#!/bin/bash
set -euo pipefail

find_brew() {
    if command -v brew >/dev/null 2>&1; then
        command -v brew
    elif [[ -x /opt/homebrew/bin/brew ]]; then
        printf '%s\n' /opt/homebrew/bin/brew
    elif [[ -x /usr/local/bin/brew ]]; then
        printf '%s\n' /usr/local/bin/brew
    else
        return 1
    fi
}

main() {
    if [[ "$(uname -s)" != Darwin ]]; then
        printf '%s\n' 'this installer is for macos.' >&2
        return 1
    fi

    local brew_bin brew_env installer source_dir
    source_dir="$HOME/projects/dotfiles"

    if ! brew_bin="$(find_brew)"; then
        installer="$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        /bin/bash -c "$installer"
        brew_bin="$(find_brew)"
    fi

    brew_env="$("$brew_bin" shellenv)"
    eval "$brew_env"
    "$brew_bin" install chezmoi

    chezmoi --source "$source_dir" init https://github.com/scythe0x/dotfiles.git
    "$brew_bin" bundle install --file="$source_dir/Brewfile" --no-upgrade
    chezmoi --source "$source_dir" apply

    printf '%s\n' 'done. open a new terminal to load your zsh settings.'
}

if [[ -z "${BASH_SOURCE[0]:-}" || "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
