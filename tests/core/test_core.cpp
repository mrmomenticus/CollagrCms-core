
#include <catch2/catch_test_macros.hpp>
#include <list>
#include "src/core/core.hpp"
#include "src/core/image.hpp"

auto imageCreated = ImageCreated();

auto images = std::list<Image>{
    Image{"tests/core/img/input/1.jpg", "Description 1", "1000P"},
    Image{"tests/core/img/input/2.jpg", "Description 2", "5000P"},
    Image{"tests/core/img/input/3.jpg",
          "Descriptionwqfqwfqwfqwfqwfqwfqwfffffffffffffffffffffffffffffffffffffffffffqfwqffffffffff"
          "ffffffffwqfqf 3",
          "300P"},
    Image{"tests/core/img/input/4.jpg", "Description 4", "250P"},
    Image{"tests/core/img/input/5.jpg",
          "Descriffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
          "ffffffffffffffffffffffffffffffffffffffffffffffffffffffption 5",
          "600P"},
    Image{"tests/core/img/input/6.jpg", "Description 6", "780P"},
    Image{"tests/core/img/input/7.jpg", "Description 7", "260P"},
    Image{"tests/core/img/input/8.jpeg", "Description 8", "10000P"},
    Image{"tests/core/img/input/9.jpg", "Description 9", "500000P"}};
TEST_CASE("Test created output image")
{
    const std::string outputPath = "tests/core/img/output/collage.jpg";
    auto              test       = imageCreated.create(images, outputPath);

    REQUIRE(test.empty() == false);
}
