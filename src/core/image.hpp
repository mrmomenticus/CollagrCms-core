class Image final 
{

public:
    Image() = default; 
    Image(std::string_view path, std::string_view description, int32_t price) : _path(path), _description(description), _price(price) {};


private:
    const std::string_view _path;
    const std::string_view _description;
    const int32_t _price;
};