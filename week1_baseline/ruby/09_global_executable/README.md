# Step 8 — Global Executable

Package BOUKENSHA as a gem so the `boukensha` command works from anywhere on your machine.

## What this step adds

- `boukensha.gemspec` — declares the gem: name, version, which files to include, and the `bin/boukensha` executable
- `bin/boukensha` — the shebang script that becomes the global command
- `lib/boukensha_loader.rb` — resolves *which step folder* to load from, then boots the REPL
- `lib/boukensha.rb` + `lib/boukensha/` — step 7's lib, bundled as the default

## Install

```bash
cd 08_global_executable
gem build boukensha.gemspec
gem install boukensha-0.9.0.gem
```

After that, `boukensha` is on your `$PATH` and works from any directory.

## Switching steps with BOUKENSHA_PATH

The loader resolves in this order:

| Priority | Source | Example |
|----------|--------|---------|
| 1 | `BOUKENSHA_PATH` env var | `BOUKENSHA_PATH=~/Sites/boukensha/07_the_repl_loop boukensha` |
| 2 | `path:` in `~/.boukensharc` | see below |
| 3 | Bundled default | just run `boukensha` |

`BOUKENSHA_PATH` must point to a step folder that contains `lib/boukensha.rb`.

## ~/.boukensharc

`~/.boukensharc` is a YAML file that can set both the step path and the config directory:

```yaml
# ~/.boukensharc
path: ~/Sites/boukensha/07_the_repl_loop   # which step lib to load
dir:  ~/.my_boukensha_config               # where settings.yaml / .env live
```

Both keys are optional — omit either to fall back to the default. The config directory (`dir`) can also be overridden at runtime with `BOUKENSHA_DIR`.

| Setting | Priority 1 | Priority 2 | Priority 3 |
|---------|-----------|-----------|-----------|
| Step lib | `BOUKENSHA_PATH` env var | `path:` in `~/.boukensharc` | bundled default |
| Config dir | `BOUKENSHA_DIR` env var | `dir:` in `~/.boukensharc` | `~/.boukensha` |

A bare path (old single-line format) in `~/.boukensharc` is still accepted as `path` for backwards compatibility.

## Running a specific step

```bash
# step 7 (interactive REPL)
BOUKENSHA_PATH=~/Sites/boukensha/07_the_repl_loop boukensha

# step 6 doesn't have a REPL — loader tells you how to run it
BOUKENSHA_PATH=~/Sites/boukensha/06_the_run_dsl boukensha
# => boukensha: the step at .../06_the_run_dsl does not support the interactive REPL
#    Run its examples directly, e.g.: ruby .../06_the_run_dsl/examples/*.rb
```

## Debug mode

```bash
BOUKENSHA_DEBUG=1 boukensha
# => [boukensha] loading from: /path/to/step
```

## The key idea

The gem is just a **wrapper and a default**. All the teaching material stays in the numbered step folders exactly as it was. The gem doesn't copy or symlink anything — it just knows where to look.
