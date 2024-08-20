venv_path := ".venv/bin"

default:
    @just --list --justfile {{justfile()}}

playbook *ARGS:
    {{venv_path}}/ansible-playbook --inventory hosts playbook.yml {{ARGS}}

lint:
    {{venv_path}}/ansible-lint

cmdb:
    {{venv_path}}/ansible --inventory hosts --module-name ansible.builtin.setup --tree out/ all
    {{venv_path}}/ansible-cmdb --inventory hosts out/ > overview.html

todo:
    grep --recursive --extended-regexp --ignore-case --line-number --color=always 'noqa|todo' roles
