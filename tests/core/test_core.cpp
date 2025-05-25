
#include <catch2/catch_test_macros.hpp>
#include <list>
#include "src/core/core.hpp"
#include "src/core/image.hpp"

auto imageCreated = ImageCreated();

auto images = std::list<Image>{Image{"tests/core/img/input/1.jpg", "Description 1", "1000"},
                               Image{"tests/core/img/input/2.jpg", "Description 2", "5000"},
                               Image{"tests/core/img/input/3.jpg", "Descriptionwqfqwfqwfqwfqwfqwfqwfffffffffffffffffffffffffffffffffffffffffffqfwqffffffffffffffffffwqfqf 3", "300"},
                               Image{"tests/core/img/input/4.jpg", "Description 4", "250"},
                               Image{"tests/core/img/input/5.jpg", "Descriffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffption 5", "600"},
                               Image{"tests/core/img/input/6.jpg", "Description 6", "780"},
                               Image{"tests/core/img/input/7.jpg", "Description 7", "260"},
                               Image{"tests/core/img/input/8.jpeg", "Description 8", "10000"},
                               Image{"tests/core/img/input/9.jpg", "Description 9", "500000"}};
TEST_CASE("Test created output image")
{
    const std::string outputPath = "tests/core/img/output/collage.jpg";
    auto              test       = imageCreated.create(images, outputPath);

    REQUIRE(test.empty() == false);
}
