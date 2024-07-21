venv_path := ".venv/bin"

default:
    @just --list --justfile {{justfile()}}

playbook:
    {{venv_path}}/ansible-playbook --inventory hosts playbook.yml

cmdb:
    {{venv_path}}/ansible --inventory hosts --module-name ansible.builtin.setup --tree out/ all
    {{venv_path}}/ansible-cmdb --inventory hosts out/ > overview.html
