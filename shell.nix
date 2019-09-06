with import <nixpkgs> {};

let python = python3;
    env = python.buildEnv.override {
      extraLibs = with python.pkgs;
        [ zeroc-ice
          requests
          sleekxmpp
        ];
    };

in env.env
