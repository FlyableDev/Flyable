#ifndef FormatReader_HPP_INCLUDED
#define FormatReader_HPP_INCLUDED
#include <vector>
#include <string>

class FormatReader
{
public:

    FormatReader();
    FormatReader(char* data,int size);

    int readInt32();
    long long readInt64();
    float readFloat();
    double readDouble();
    std::string readString();

    FormatReader sub(int size);

    char* getData();
    int getDataSize();
    unsigned int getCurrentIndex();

    bool atEnd();

private:
    std::vector<char> mData;
    unsigned int mCurrentIndex;
};


#endif // FormatReader_HPP_INCLUDED
