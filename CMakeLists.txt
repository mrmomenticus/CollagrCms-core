cmake_minimum_required(VERSION 4.0)

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

# grpc
find_package(gRPC REQUIRED)
target_link_libraries(${PROJECT_NAME} gRPC::grpc++)
find_package(Protobuf REQUIRED)
target_link_libraries(${PROJECT_NAME} protobuf::libprotobuf)


# compiler options
target_compile_features( ${PROJECT_NAME}
    PRIVATE
    cxx_std_23
)

# tests
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.8.1 # or a later release
)

FetchContent_MakeAvailable(Catch2)




# tests
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.8.1 # or a later release
)

FetchContent_MakeAvailable(Catch2)
include(${CMAKE_CURRENT_LIST_DIR}/tests/test.cmake)
# Create test executable
add_executable(test_${PROJECT_NAME}
    tests/test.cpp
    ${test_${PROJECT_NAME}-source}
    ${COLLAGRCMS_SOURCE} # Add program sources directly
)



# Include directories for tests
target_include_directories(
    test_${PROJECT_NAME}
    PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}/
    ${COLLAGRCMS_INCLUDE}
)

# Link only with external libraries (NOT with ${PROJECT_NAME}_lib!)
target_link_libraries(test_${PROJECT_NAME} 
    PRIVATE 
    Catch2::Catch2WithMain
    ${OpenCV_LIBS}
    gRPC::grpc++
    protobuf::libprotobuf
)

target_compile_features(
    test_${PROJECT_NAME}
    PRIVATE
    cxx_std_23
)
