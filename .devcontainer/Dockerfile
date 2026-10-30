# Imagen común a los dos entornos (cpu y gpu).
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# La imagen base trae el repositorio de Yarn con la clave GPG caducada (NO_PUBKEY 62D54FD4003F6525):
# apt-get update falla y las features no se instalan. Yarn no se usa (la web va con pnpm).
RUN rm -f /etc/apt/sources.list.d/yarn.list
