# BoukenshaLoader resolves which step folder to load from, then boots the REPL.
#
# Resolution order for the step lib (BOUKENSHA_PATH):
#   1. BOUKENSHA_PATH environment variable
#   2. `path:` key in ~/.boukensharc
#   3. The lib/ directory bundled inside this gem (the latest release)
#
# Resolution order for the config directory (BOUKENSHA_DIR):
#   1. BOUKENSHA_DIR environment variable
#   2. `dir:` key in ~/.boukensharc
#   3. ~/.boukensha  (default)
#
# ~/.boukensharc is a YAML file, e.g.:
#   path: ~/Sites/boukensha/07_the_repl_loop
#   dir:  ~/.my_boukensha_config
#
# A bare path (old single-line format) is still accepted for backwards compatibility.
#
# Examples:
#   boukensha                                                   # uses bundled lib + ~/.boukensha
#   BOUKENSHA_PATH=~/Sites/boukensha/04_api_client boukensha   # loads step 4
#   BOUKENSHA_DIR=~/projects/mybot/.boukensha boukensha        # custom config dir
module BoukenshaLoader
  require "yaml"

  # Absolute path to this gem's own bundled boukensha lib.
  BUNDLED_LIB = File.expand_path("../boukensha.rb", __FILE__)

  # Parse ~/.boukensharc as YAML.
  # Accepts a plain hash with optional `path` and `dir` keys.
  # A bare string (old single-line format) is treated as `path` for backwards compatibility.
  def self.parse_rc(rc_path)
    data = YAML.safe_load(File.read(rc_path)) || {}
    data.is_a?(String) ? { "path" => data } : data
  rescue Psych::SyntaxError => e
    abort "boukensha: ~/.boukensharc is not valid YAML: #{e.message}"
  end

  def self.resolve
    # 1. Env var wins.
    if ENV["BOUKENSHA_PATH"]
      dir  = File.expand_path(ENV["BOUKENSHA_PATH"])
      main = File.join(dir, "lib", "boukensha.rb")
      return main if File.exist?(main)

      abort <<~MSG
        boukensha: BOUKENSHA_PATH is set but no lib/boukensha.rb found at:
               #{dir}
               Make sure BOUKENSHA_PATH points to a step folder, e.g.:
               BOUKENSHA_PATH=~/Sites/boukensha/07_the_repl_loop boukensha
      MSG
    end

    # 2. ~/.boukensharc
    rc = File.expand_path("~/.boukensharc")
    if File.exist?(rc)
      conf = parse_rc(rc)

      # Apply dir before anything else so Config picks it up via BOUKENSHA_DIR.
      if conf["dir"] && !ENV["BOUKENSHA_DIR"]
        ENV["BOUKENSHA_DIR"] = File.expand_path(conf["dir"])
      end

      if (raw_path = conf["path"]) && !raw_path.strip.empty?
        main = File.join(File.expand_path(raw_path), "lib", "boukensha.rb")
        return main if File.exist?(main)

        abort <<~MSG
          boukensha: ~/.boukensharc `path` points to #{raw_path}
                 but no lib/boukensha.rb was found there.
                 Update ~/.boukensharc or remove the path key to use the bundled default.
        MSG
      end
    end

    # 3. Bundled default.
    BUNDLED_LIB
  end

  def self.load_and_start_repl
    main = resolve
    step_dir = File.dirname(File.dirname(main))

    puts "[boukensha] loading from: #{step_dir}" if ENV["BOUKENSHA_DEBUG"]

    require main

    unless Boukensha.respond_to?(:repl)
      abort <<~MSG
        boukensha: the step at #{step_dir}
               does not support the interactive REPL (added in step 7).
               Run its examples directly, e.g.:
                 ruby #{step_dir}/examples/*.rb
               Or point BOUKENSHA_PATH at step 7 or later.
      MSG
    end

    Boukensha.repl
  end
end
