cmake_minimum_required(VERSION 3.22)

project(collagrcms_core VERSION 0.1.0 LANGUAGES C CXX)

include( ${PROJECT_SOURCE_DIR}/src/src.cmake )

add_executable(collagrcms_core src/main.cpp)

# source files
target_sources( ${PROJECT_NAME}
    PRIVATE
    ${PROJECT_SOURCE_DIR}/src/main.cpp
    ${COLLAGRCMS_SOURCE}
)
# include directories
target_include_directories( ${PROJECT_NAME}
    PRIVATE
    ${COLLAGRCMS_INCLUDE}
)
# libraries
include(FetchContent)
# opencv
FetchContent_Declare(
        opencv
        GIT_REPOSITORY https://github.com/opencv/opencv.git
        GIT_TAG 4.11.0
        GIT_SHALLOW TRUE
        GIT_PROGRESS TRUE
)
FetchContent_MakeAvailable(opencv)
target_include_directories(${PROJECT_NAME} PRIVATE
        ${OPENCV_CONFIG_FILE_INCLUDE_DIR}
        ${OPENCV_MODULE_opencv_core_LOCATION}/include
        )
target_link_libraries(${PROJECT_NAME} ${OpenCV_LIBS})

#grpc protobuf

# FetchContent_Declare(
#         grpc
#         GIT_REPOSITORY https://github.com/grpc/grpc.git
#         GIT_TAG v1.72.0
#         GIT_SHALLOW TRUE
# )
# set(FETCHCONTENT_QUIET OFF)
# FetchContent_MakeAvailable(gRPC)
# target_link_libraries(${PROJECT_NAME} grpc++)
find_package(gRPC REQUIRED)
target_link_libraries(${PROJECT_NAME} gRPC::grpc++)
find_package(Protobuf REQUIRED)
target_link_libraries(${PROJECT_NAME} protobuf::libprotobuf)


# compiler options
target_compile_features( ${PROJECT_NAME}
    PRIVATE
    cxx_std_23
)

