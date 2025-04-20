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
                validate-card-data = {
                  enable = true;
                  name = "Validate Card Data";
                  entry = "uv run python ./validators/card_data.py";
                  language = "system";
                  # Run only when TOML files in card_data/ change
                  files = "^card_data/";
                  types = [ "toml" ];
                  pass_filenames = false; # The script reads the directory directly
                };
              };
            };
          };

          # When execute `nix develop`, you go in shell installed nil.
          devenv.shells.default = {
            packages = with pkgs; [
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
