cmake_minimum_required(VERSION 3.31)
project(collagrcms_core VERSION 0.1.0 LANGUAGES C CXX)

include( ${PROJECT_SOURCE_DIR}/src/src.cmake )

add_executable(collagrcms_core src/main.cpp)

target_compile_features(
    ${PROJECT_NAME}
    PRIVATE
    cxx_std_23 
)
target_compile_options( ${PROJECT_NAME} 
    PRIVATE -Wall)


# LIBRARIES
include(FetchContent)
FetchContent_Declare(
  spdlog
  GIT_REPOSITORY https://github.com/gabime/spdlog.git
  GIT_TAG        v1.15.3 # or a later release
)
FetchContent_MakeAvailable(spdlog)

find_package(OpenCV REQUIRED)
# find_package(gRPC REQUIRED)
# find_package(Protobuf REQUIRED)
message(STATUS "OpenCV_LIBS: ${OpenCV_LIBS}" "OpenCV include" ${OpenCV_INCLUDE_DIRS})  
target_include_directories(${PROJECT_NAME} PRIVATE ${OPENCV_INCLUDE_DIRS})
# target_link_libraries(${PROJECT_NAME} ${OpenCV_LIBS} gRPC::grpc++ protobuf::libprotobuf spdlog::spdlog)
target_link_libraries(${PROJECT_NAME} ${OpenCV_LIBS} spdlog::spdlog)
# message("OpenCV Version ${OpenCV_VERSION}, gRPC Version ${gRPC_VERSION}, Protobuf Version ${Protobuf_VERSION} , spdlog Version ${spdlog_VERSION}")
message("OpenCV Version ${OpenCV_VERSION}, spdlog Version ${spdlog_VERSION}")

# SOURCES
target_sources( ${PROJECT_NAME}
    PRIVATE
    ${PROJECT_SOURCE_DIR}/src/main.cpp
    ${COLLAGRCMS_SOURCE}
)

# INCLUDE
target_include_directories( ${PROJECT_NAME}
    PRIVATE
    ${COLLAGRCMS_INCLUDE}
)

# TESTS
FetchContent_Declare(
  Catch2
  GIT_REPOSITORY https://github.com/catchorg/Catch2.git
  GIT_TAG        v3.8.1 # or a later release
)

FetchContent_MakeAvailable(Catch2)
include(${CMAKE_CURRENT_LIST_DIR}/tests/test.cmake)

add_executable(test_${PROJECT_NAME}
    tests/test.cpp
    ${test_${PROJECT_NAME}-source}
    ${COLLAGRCMS_SOURCE} # Add program sources directly
)

target_include_directories(
    test_${PROJECT_NAME}
    PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}/
    ${COLLAGRCMS_INCLUDE}
    ${OPENCV_INCLUDE_DIRS}
)

target_link_libraries(test_${PROJECT_NAME} 
    PRIVATE 
    Catch2::Catch2WithMain
    ${OpenCV_LIBS} gRPC::grpc++ protobuf::libprotobuf spdlog::spdlog
)

target_compile_features(
    test_${PROJECT_NAME}
    PRIVATE
    cxx_std_23
)
