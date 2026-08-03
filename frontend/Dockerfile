# ---- Build stage ----
FROM node:20-alpine AS build
WORKDIR /app

# The lockfile is copied too, and `npm ci` installs strictly from it: two builds
# of the same commit produce the same dependency tree. `npm install` without the
# lockfile re-resolves versions on every build.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# The subpath the app is served under (e.g. "/qoldau/"). Drives Vite base,
# the router basename, and the same-origin API URL. Defaults to root.
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=$VITE_BASE_PATH
RUN npm run build

# ---- Serve stage ----
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
