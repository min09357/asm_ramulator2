
set -e

rm -rf ./build
rm -rf ./ramulator2

mkdir build
cd build
cmake ..
make -j6
cp ./ramulator2 ../ramulator2
cd ..