#ifndef CODEGEN_HPP_INCLUDED
#define CODEGEN_HPP_INCLUDED
#include <iostream>
#include <vector>
#include "FormatReader.hpp"
#include "llvm/IR/LLVMContext.h"
#include "llvm/IR/Module.h"
#include "llvm/IR/BasicBlock.h"
#include "llvm/IR/Function.h"
#include "llvm/IR/Constants.h"
#include "llvm/IR/IRBuilder.h"
#include "llvm/IR/GlobalVariable.h"
#include "llvm/IR/PassManager.h"
#include "llvm/IR/Attributes.h"
#include "llvm/Support/raw_os_ostream.h"
#include "llvm/Support/raw_ostream.h"
#include "llvm/Bitcode/BitcodeWriter.h"
#include "llvm/Support/TargetSelect.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/TargetRegistry.h"
#include "llvm/IR/LegacyPassManager.h"
#include "llvm/IR/Verifier.h"
#include "llvm/Target/TargetOptions.h"
#include "llvm/Target/TargetMachine.h"

#ifdef _WIN32
    #define EXPORT_FUNC __declspec(dllexport) _cdecl
#else
    #define EXPORT_FUNC __attribute__((visibility("default")))
#endif // _WIN32


extern "C"
{
    EXPORT_FUNC void flyable_codegen_run(char* data,int size,char* output);
};

enum TypePrimitive
{
    INT1 = 0,
    INT8 = 1,
    INT16 = 2,
    INT32 = 3,
    INT64 = 4,
    FLOAT = 5,
    DOUBLE = 6,
    VOID = 7,
    STRUCT = 8,
};

class CodeGen
{
public:
    CodeGen();
    void init();
    void output(std::string output);
    void readInput(FormatReader& reader);

private:

    void readStructs(FormatReader& reader);
    void readGlobalVars(FormatReader& reader);
    void readFuncs(FormatReader& reader);
    void readBody(llvm::Function* func,std::vector<llvm::Value*>&values,std::vector<FormatReader> &readers,std::vector<std::string>& blockNames);

    void printType(llvm::Type* type);
    bool isDecimalType(llvm::Value* value);
    bool isDecimalType(llvm::Type* type);

    std::vector<llvm::StructType*>mStructTypes;
    std::vector<llvm::GlobalVariable*>mGlobalVars;
    std::vector<llvm::Function*>mFuncs;

    llvm::Type* readType(FormatReader& reader);
    llvm::GlobalValue::LinkageTypes readLinkage(FormatReader& reader);


    llvm::LLVMContext mContext;
    llvm::DataLayout* mLayout;
    llvm::Module* mModule;
    const llvm::Target* mTarget;
    llvm::TargetMachine* mTargetMachine;
    llvm::IRBuilder<> mBuilder;
};



#endif // CODEGEN_HPP_INCLUDED
