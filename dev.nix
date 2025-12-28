# dev.nix
{ pkgs, ... }: {
  # Enable the Docker daemon service
  services.docker.enable = true;

  # Packages to install in the environment
  packages = [
    pkgs.python311
    pkgs.poetry
    pkgs.ffmpeg           # Required for viewing/processing video
    pkgs.docker-compose   # Useful for orchestrating services later
  ];

  # Environment variables
  env = {
    POETRY_VIRTUALENVS_IN_PROJECT = "true";
  };

  # IDX-specific lifecycle hooks
  idx = {
    extensions = [
      "ms-python.python"
      "tamasfe.even-better-toml"
    ];
    workspace = {
      # Runs when workspace is first created
      onCreate = {
        install = "poetry install";
      };
      # Runs every time workspace starts
      onStart = {
        # Ensure the docker socket is accessible
        check-docker = "docker --version"; 
      };
    };
  };
}
