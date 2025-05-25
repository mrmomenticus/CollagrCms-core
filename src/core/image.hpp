#pragma once
#include <string>


class Image final 
{

public:
    Image(std::string path, std::string description, std::string price) : path(path), description(description), price(price) {};

    std::string path;
    std::string description;
    std::string price;
};