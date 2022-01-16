#include "FormatReader.hpp"


FormatReader::FormatReader()
{
    mCurrentIndex = 0;
}

FormatReader::FormatReader(char* data,int size)
{
    mData = std::vector<char>(data,data + size);
    mCurrentIndex = 0;
}

int FormatReader::readInt32()
{
    int* result = (int*) &mData[mCurrentIndex];
    mCurrentIndex += sizeof(int);
    return *result;
}

long long FormatReader::readInt64()
{
    long long* result = (long long*) &mData[mCurrentIndex];
    mCurrentIndex += sizeof(long long);
    return *result;
}

float FormatReader::readFloat()
{
    float* result = (float*) &mData[mCurrentIndex];
    mCurrentIndex += sizeof(float);
    return *result;
}

double FormatReader::readDouble()
{
    double* result = (double*) &mData[mCurrentIndex];
    mCurrentIndex += sizeof(double);
    return *result;
}

std::string FormatReader::readString()
{
    std::string result = "";
    int size = readInt32();
    for(int i = 0;i < size;++i)
        result += mData[mCurrentIndex + i];
    mCurrentIndex += size;
    return result;
}

FormatReader FormatReader::sub(int size)
{
    FormatReader result;
    auto first = mData.begin() + mCurrentIndex;
    auto end = first + size;
    result.mData = std::vector<char>(first,end);
    mCurrentIndex += size;
    return result;
}

char* FormatReader::getData()
{
    return &mData[0];
}

int FormatReader::getDataSize()
{
    return mData.size();
}

void FormatReader::setCurrentIndex(unsigned int index)
{
    mCurrentIndex = index;
}

unsigned int FormatReader::getCurrentIndex()
{
    return mCurrentIndex;
}

bool FormatReader::atEnd()
{
    return mCurrentIndex >= mData.size();
}

