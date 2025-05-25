#pragma once
#include "image.hpp"
#include <list>
#include <string_view>
class ImageCreated final 
{

public:
    ImageCreated() {};
    ImageCreated(ImageCreated &&) = delete;
    ImageCreated && operator=(const ImageCreated &) = delete;
    ImageCreated(const ImageCreated &) = delete;
    ImageCreated & operator=(ImageCreated &&) = delete;

    
    const std::string_view create(std::list<Image> &images, const std::string &outputPath);

};