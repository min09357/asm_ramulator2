
set -e

rm -rf ./build
rm -rf ./ramulator2

mkdir build
cd build
cmake ..
make -j$(( $(nproc) * 3 / 4 ))
cp ./ramulator2 ../ramulator2
cd ..