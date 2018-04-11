with import <nixpkgs> {};

let python = python3;
  env = python.buildEnv.override {
  extraLibs = with python.pkgs;
    [ systemd
    ];
};

in env.env
