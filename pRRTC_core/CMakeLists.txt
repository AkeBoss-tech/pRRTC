cmake_minimum_required(VERSION 3.16...3.22)

# Use system compiler (don't force clang++ - not available on all clusters)
# find_program(CLANGPP "clang++")
# set(CMAKE_CXX_COMPILER ${CLANGPP} CACHE STRING "C++ compiler" FORCE)

include(FetchContent)
FetchContent_Declare(json URL https://github.com/nlohmann/json/releases/download/v3.11.3/json.tar.xz)
FetchContent_MakeAvailable(json)


project (
    batched_cc
    VERSION 0.0
    LANGUAGES CXX CUDA
)

set(CMAKE_CUDA_SEPARABLE_COMPILATION ON)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CUDA_ARCHITECTURES 86)

# Try to find Eigen3 via CMake config, else use hardcoded Amarel path
find_package(Eigen3 3.3 QUIET NO_MODULE)
if(NOT Eigen3_FOUND)
    message(STATUS "Eigen3 CMake config not found, using hardcoded Amarel path")
    # Create interface library for Eigen3
    add_library(Eigen3::Eigen INTERFACE IMPORTED)
    set_target_properties(Eigen3::Eigen PROPERTIES
        INTERFACE_INCLUDE_DIRECTORIES "/projects/community/eigen/3.3.4/gc563/include"
    )
endif()


# set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -Xptxas -v")
# set(CMAKE_CUDA_FLAGS ${CMAKE_CUDA_FLAGS} "-g -G")  # enable cuda-gdb
# set(CMAKE_CUDA_FLAGS ${CMAKE_CUDA_FLAGS} "-lineinfo")  # enable line info in ncu ui


### motion benchmark script
add_executable(evaluate_mbm
    scripts/evaluate_mbm.cpp
    src/planning/pRRTC.cu
)

target_include_directories(evaluate_mbm
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/build/_deps/nigh-src/src
    ${CMAKE_CURRENT_SOURCE_DIR}/build/_deps/pdqsort-src
    /projects/community/eigen/3.3.4/gc563/include
    /projects/community/eigen/3.3.4/gc563/include/eigen3
    ${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES}
)


target_link_libraries(evaluate_mbm
    PRIVATE
    nlohmann_json::nlohmann_json
    Eigen3::Eigen
)

target_compile_options(evaluate_mbm PRIVATE
    -Wno-c++11-narrowing
)

### single_mbm
add_executable(single_mbm
    scripts/single_mbm.cpp
    src/planning/pRRTC.cu
)

target_include_directories(single_mbm
    PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/build/_deps/nigh-src/src
    ${CMAKE_CURRENT_SOURCE_DIR}/build/_deps/pdqsort-src
    /projects/community/eigen/3.3.4/gc563/include
    /projects/community/eigen/3.3.4/gc563/include/eigen3
    ${CMAKE_CUDA_TOOLKIT_INCLUDE_DIRECTORIES}
)

target_link_libraries(single_mbm
    PRIVATE
    nlohmann_json::nlohmann_json
    Eigen3::Eigen
)

target_compile_options(single_mbm PRIVATE
    -Wno-c++11-narrowing
)