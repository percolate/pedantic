set -ex

# docker hub username
USERNAME=julienfunk
# image name
IMAGE=pedantic

# ensure we're up to date
git pull

# bumps the version
docker run --rm -v "$PWD":/app treeder/bump patch

version=`cat VERSION`
echo "version: ${version}"

# run build
docker build -t ${USERNAME}/${IMAGE} .

# tag it
git commit -m "version ${version}"
git tag -a "${version}" -m "version ${version}"
git push
git push --tags
docker tag ${USERNAME}/${IMAGE}:latest ${USERNAME}/${IMAGE}:${version}

# push it
docker push ${USERNAME}/${IMAGE}:latest
docker push ${USERNAME}/${IMAGE}:${version}
