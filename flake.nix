{
  description = "wikiteam3 - Nix flake for reproducible wiki archiving";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
      
      wikiteam3 = pkgs.python3Packages.buildPythonApplication {
        pname = "wikiteam3";
        version = "3.11.0";
        
        pyproject = true;
        
        src = ./.;
        
        build-system = with pkgs.python3Packages; [
          pdm-backend
        ];
        
        propagatedBuildInputs = with pkgs.python3Packages; [
          requests
          mwclient
          mwparserfromhell
          file-read-backwards
          python-slugify
        ];
        
        meta = with pkgs.lib; {
          description = "Tools for archiving wikis";
          homepage = "https://github.com/saveweb/wikiteam3";
          license = licenses.gpl3;
          maintainers = [ "Meta-Introspector Research Group" ];
        };
      };
      
    in {
      packages.${system} = {
        default = wikiteam3;
        wikiteam3 = wikiteam3;
      };
      
      apps.${system}.default = {
        type = "app";
        program = "${wikiteam3}/bin/wikiteam3dumpgenerator";
      };
      
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = [ wikiteam3 ];
      };
    };
}
