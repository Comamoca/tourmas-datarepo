{
  description = "A basic flake to with flake-parts";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixpkgs-unstable";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    flake-parts.url = "github:hercules-ci/flake-parts";
    systems.url = "github:nix-systems/default";
    git-hooks-nix.url = "github:cachix/git-hooks.nix";
    devenv.url = "github:cachix/devenv";
    nixpkgs-python.url = "github:cachix/nixpkgs-python";
    nixpkgs-python.inputs = { nixpkgs.follows = "nixpkgs"; };
  };

  outputs =
    inputs@{
      self,
      systems,
      nixpkgs,
      flake-parts,
      ...
    }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      imports = [
        inputs.treefmt-nix.flakeModule
        inputs.git-hooks-nix.flakeModule
        inputs.devenv.flakeModule
      ];
      systems = import inputs.systems;

      perSystem =
        {
          config,
          pkgs,
          system,
          ...
        }:
        let
          stdenv = pkgs.stdenv;

          git-secrets' = pkgs.writeShellApplication {
            name = "git-secrets";
            runtimeInputs = [ pkgs.git-secrets ];
            text = ''
              git secrets --scan
            '';
          };
        in
        {
          treefmt = {
            projectRootFile = "flake.nix";
            programs = {
              nixfmt.enable = true;
              taplo.enable = true;
            };

            settings.formatter = { };
          };

          pre-commit = {
            check.enable = true;
            settings = {
              hooks = {
                treefmt.enable = true;
                ripsecrets.enable = true;
                git-secrets = {
                  enable = true;
                  name = "git-secrets";
                  entry = "${git-secrets'}/bin/git-secrets";
                  language = "system";
                  types = [ "text" ];
                };
                # Validate card data using the devenv environment
                validate-card-data = {
                  enable = true;
                  name = "Validate Card Data";
                  # Wrap the command in a script executed by the devenv shell
                  entry = "${config.devenv.shells.default.pkgs.writeShellScript "validate-card-data-hook" ''
                    set -e
                    echo "Running card data validation hook..."
                    # Ensure we are in the project root relative to the script
                    cd "$(${pkgs.git}/bin/git rev-parse --show-toplevel)"
                    uv run python ./validators/card_data.py
                  ''}/bin/validate-card-data-hook";
                  language = "script"; # The entry is now a script path
                  files = "^card_data/"; # Regex matching files in card_data/
                  types = [ "toml" ];    # Only trigger for toml files
                  pass_filenames = false; # The script doesn't take filenames as args
                };
              };
            };
          };

          # When execute `nix develop`, you go in shell installed nil.
          devenv.shells.default = {
            packages = with pkgs; [
	      # For aider
	      playwright
	      ruff
              nil
            ];

            languages = {
              python = {
                enable = true;
                version = "3.13";
		uv = {
		  enable = true;
		  sync.enable = true;
		};
              };
            };

            enterShell = ''
	    '';
          };
        };
    };
}
