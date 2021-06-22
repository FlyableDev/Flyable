#include "CodeGen.hpp"
#include <iostream>
#include <fstream>

void flyable_codegen_run(char* data,int size,char* path)
{
    CodeGen gen;
    gen.init();
    FormatReader reader(data,size);
    gen.readInput(reader);
    gen.output(std::string(path));
}

CodeGen::CodeGen() : mBuilder(mContext)
{

}

void CodeGen::init()
{
    mModule = new llvm::Module("Flyable",mContext);
    llvm::InitializeNativeTarget();
    llvm::InitializeAllTargetInfos();
    llvm::InitializeAllTargets();
    llvm::InitializeAllTargetMCs();
    llvm::InitializeAllAsmParsers();
    llvm::InitializeAllAsmPrinters();

    std::string error;
    std::string targetTriple = "";
    targetTriple ="x86_64-unknown-windows-c";//llvm::sys::getDefaultTargetTriple();
    //targetTriple ="x86_64-apple-macosx10.7.0-c";//llvm::sys::getDefaultTargetTriple();
    //targetTriple = "wasm32-unknown-unknown";

    mTarget = llvm::TargetRegistry::lookupTarget(targetTriple, error);

    auto CPU = "generic";
    auto Features = "";
    llvm::TargetOptions opt;
    auto RM = llvm::Optional<llvm::Reloc::Model>();
    mTargetMachine = mTarget->createTargetMachine(targetTriple, CPU, Features, opt, RM);

    mModule->setDataLayout(mTargetMachine->createDataLayout());
    mModule->setTargetTriple(targetTriple);

    mLayout = new llvm::DataLayout(mModule);

}

void CodeGen::output(std::string output)
{
    bool hasError = false;
    auto &functionList = mModule->getFunctionList();
    for(auto &function : functionList)
    {
        std::string errorString;
        llvm::raw_string_ostream rso(errorString);
        if(llvm::verifyFunction(function,&rso))
        {
            std::cout<<function.getName().str()<<std::endl;
            std::cout<<rso.str()<<std::endl;
            std::cout<<std::endl;
            hasError = true;
        }
    }

    /*
    {
        //Uncomment to output the IR in a textual format
        std::ofstream outputFile("outputIR.txt");
        llvm::raw_os_ostream ir(outputFile);
        mModule->print(ir,nullptr);
    }
    */

    if(!hasError)
    {
        std::string filename = output;
        std::error_code EC;
        llvm::raw_fd_ostream dest(filename, EC, llvm::sys::fs::F_None);
        llvm::legacy::PassManager pass;
        if(mTargetMachine->addPassesToEmitFile(pass, dest,nullptr,llvm::CodeGenFileType::CGFT_ObjectFile))
        {
            std::cout<< "TheTargetMachine can't emit a file of this type"<<std::endl;
        }

        pass.run(*mModule);
        dest.flush();
    }
}

void CodeGen::readInput(FormatReader& reader)
{
    if(reader.readString() == "**Flyable format**")
    {
        readStructs(reader);
        readGlobalVars(reader);
        readFuncs(reader);
    }
    else
        std::cout<<"Flyable code generation format unrecognized"<<std::endl;
}



void CodeGen::readStructs(FormatReader& reader)
{
    //read all structs
    int structCount = reader.readInt32();
    mStructTypes.resize(structCount);
    for(size_t i = 0;i < structCount;++i)
    {
        mStructTypes[i] = llvm::StructType::create(mContext);
    }

    for(size_t i = 0;i < structCount;++i)
    {
        llvm::StructType* current = mStructTypes[i];
        std::string name = reader.readString();
        current->setName(name);

        std::vector<llvm::Type*> attr;
        size_t attrCount = reader.readInt32();
        for(size_t i = 0;i < attrCount;++i)
            attr.push_back(readType(reader));
        current->setBody(llvm::ArrayRef<llvm::Type*>(attr));
    }
}

void CodeGen::readGlobalVars(FormatReader& reader)
{
    //read all global var
    size_t varCount = reader.readInt32();
    mGlobalVars.resize(varCount);
    for(size_t i = 0;i < varCount;++i)
    {
        std::string name = reader.readString();
        llvm::Type* type = readType(reader);
        auto link = readLinkage(reader);
        llvm::GlobalVariable* globalVar = new llvm::GlobalVariable(*mModule,type,false,link,nullptr,name);
        globalVar->setInitializer(llvm::Constant::getNullValue(type));
        mGlobalVars[i] = globalVar;
    }
}

void CodeGen::readFuncs(FormatReader& reader)
{
    size_t funcsCount = reader.readInt32();
    mFuncs.resize(funcsCount);
    std::vector<std::vector<FormatReader>> blocks;
    std::vector<std::vector<std::string>> blockNames;
    std::vector<std::vector<llvm::Value*>> values;
    for(size_t i = 0;i < funcsCount;++i)
    {
        blocks.push_back(std::vector<FormatReader>());
        blockNames.push_back(std::vector<std::string>());
        std::string name = reader.readString();
        auto link = readLinkage(reader);

        llvm::Type* returnType = readType(reader);
        size_t argsCount = reader.readInt32();
        std::vector<llvm::Type*> argTypes;
        for(size_t j = 0;j < argsCount;++j)
        {
            argTypes.push_back(readType(reader));
        }

        llvm::FunctionType* funcType = llvm::FunctionType::get(returnType,llvm::ArrayRef<llvm::Type*>(argTypes),false);
        mFuncs[i] = llvm::Function::Create(funcType,link,name,mModule);

        size_t valuesCount = reader.readInt32();
        values.push_back(std::vector<llvm::Value*>(valuesCount));
        size_t blocksCount = reader.readInt32();
        for(size_t j = 0;j < blocksCount;++j)
        {
            blockNames[i].push_back(reader.readString());
            blocks[i].push_back(reader.sub(reader.readInt32()));
        }
    }

    for(size_t i = 0;i < mFuncs.size();++i)
    {
        readBody(mFuncs[i],values[i],blocks[i],blockNames[i]);
    }
}

void CodeGen::readBody(llvm::Function* func,std::vector<llvm::Value*>& values,std::vector<FormatReader> &readers,std::vector<std::string>& blockNames)
{
    std::vector<llvm::BasicBlock*> blocks(readers.size());
    for(size_t i = 0;i < readers.size();++i)
        blocks[i] = llvm::BasicBlock::Create(mContext,blockNames[i],func);

    size_t i = 0;
    for(auto it = func->arg_begin();it != func->arg_end();it++)
    {
        values[i] = it;
        ++i;
    }

    for(size_t i = 0;i < readers.size();++i)
    {
        FormatReader* current = &readers[i];
        mBuilder.SetInsertPoint(blocks[i]);
        while(!current->atEnd())
        {
            int opcode = current->readInt32();
            switch(opcode)
            {

                case 1:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFAdd(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateAdd(left,right);
                }
                break;

                case 2:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateSub(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateFSub(left,right);
                }
                break;

                case 3:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFMul(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateMul(left,right);
                }
                break;

                case 4:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFDiv(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateSDiv(left,right);
                }
                break;

                case 5:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFCmpOEQ(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateICmpEQ(left,right);
                }
                break;

                case 6:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFCmpONE(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateICmpNE(left,right);
                }
                break;

                case 7:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFCmpOLT(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateICmpSLT(left,right);
                }
                break;

                case 8:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFCmpOLE(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateICmpSLE(left,right);
                }
                break;

                case 9:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFCmpOGT(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateICmpSGT(left,right);
                }
                break;

                case 10:
                {
                    llvm::Value* left = values[current->readInt32()];
                    llvm::Value* right = values[current->readInt32()];
                    if(isDecimalType(left))
                        values[current->readInt32()] = mBuilder.CreateFCmpOGE(left,right);
                    else
                        values[current->readInt32()] = mBuilder.CreateICmpSGE(left,right);
                }
                break;

                case 11:
                {
                      llvm::Value* value = values[current->readInt32()];
                      if(isDecimalType(value))
                        values[current->readInt32()] = mBuilder.CreateFNeg(value);
                      else
                        values[current->readInt32()] = mBuilder.CreateNeg(value);
                }
                break;

                case 100:
                {
                    llvm::Value* value = values[current->readInt32()];
                    llvm::Value* store = values[current->readInt32()];
                    values[current->readInt32()] = mBuilder.CreateStore(value,store);
                }
                break;

                case 101:
                {
                    int id = current->readInt32();
                    values[current->readInt32()] = mBuilder.CreateLoad(values[id]);
                }
                break;

                case 150:
                    mBuilder.CreateBr(blocks[current->readInt32()]);
                break;

                case 151:
                {
                    llvm::Value* value = values[current->readInt32()];
                    llvm::BasicBlock* blockTrue = blocks[current->readInt32()];
                    llvm::BasicBlock* blockFalse = blocks[current->readInt32()];
                    mBuilder.CreateCondBr(value,blockTrue,blockFalse);
                }
                break;

                case 152:
                {
                    llvm::Value* element = values[current->readInt32()];
                    llvm::Value* indice = values[current->readInt32()];
                    values[current->readInt32()] = mBuilder.CreateGEP(element,indice);
                }
                break;

                case 153:
                {
                    llvm::Function* funcToCall = mFuncs[current->readInt32()];
                    std::vector<llvm::Value*> args(current->readInt32());
                    for(size_t i = 0;i < args.size();++i)
                    {
                        int id = current->readInt32();
                        args[i] = values[id];
                    }

                    values[current->readInt32()] = mBuilder.CreateCall(funcToCall,llvm::ArrayRef<llvm::Value*>(args));
                }
                break;

                case 1000:
                {
                    long long constVal = current->readInt64();
                    values[current->readInt32()] = mBuilder.getInt64(constVal);
                }
                break;

                case 1001:
                {
                    int constVal = current->readInt32();
                    values[current->readInt32()] = mBuilder.getInt32(constVal);
                }
                break;

                case 1002:
                {
                    int constVal = current->readInt32();
                    values[current->readInt32()] = mBuilder.getInt16(constVal);
                }
                break;

                case 1003:
                {
                    int constVal = current->readInt32();
                    values[current->readInt32()] = mBuilder.getInt8(constVal);
                }
                break;

                case 1004:
                {
                    float constVal = current->readFloat();
                    values[current->readInt32()] = llvm::ConstantFP::get(llvm::Type::getFloatTy(mContext),llvm::APFloat(constVal));
                }
                break;

                case 1005:
                {
                    double constVal = current->readDouble();
                    values[current->readInt32()] = llvm::ConstantFP::get(llvm::Type::getDoubleTy(mContext),llvm::APFloat(constVal));
                }
                break;

                case 1007:
                {
                    int constVal = current->readInt32();
                    values[current->readInt32()] = mBuilder.getInt1(constVal);
                }
                break;

                case 1006:
                {
                    llvm::Value* value;
                    llvm::Type* type = readType(*current);
                     if(type == llvm::Type::getInt64Ty(mContext))
                        value = llvm::ConstantInt::get(llvm::Type::getInt64Ty(mContext),llvm::APInt(64,0));
                    else if(type == llvm::Type::getInt32Ty(mContext))
                        value = llvm::ConstantInt::get(llvm::Type::getInt32Ty(mContext),llvm::APInt(32,0));
                    else if(type == llvm::Type::getInt16Ty(mContext))
                        value = llvm::ConstantInt::get(llvm::Type::getInt16Ty(mContext),llvm::APInt(16,0));
                    else if(type == llvm::Type::getInt8Ty(mContext))
                        value = llvm::ConstantInt::get(llvm::Type::getInt8Ty(mContext),llvm::APInt(8,0));
                    else if(type == llvm::Type::getFloatTy(mContext))
                        value = llvm::ConstantFP::get(llvm::Type::getFloatTy(mContext),llvm::APFloat(0.0));
                    else if(type == llvm::Type::getDoubleTy(mContext))
                        value = llvm::ConstantFP::get(llvm::Type::getDoubleTy(mContext),llvm::APFloat(0.0));
                    else if(type == llvm::Type::getInt1Ty(mContext))
                        value = llvm::ConstantInt::get(mContext,llvm::APInt(1,0));
                    else
                        value = llvm::ConstantPointerNull::get((llvm::PointerType*) type);

                    values[current->readInt32()] = value;
                }
                break;

                case 1010:
                {
                    llvm::Value* value = values[current->readInt32()];
                    llvm::Type* type = readType(*current);
                    values[current->readInt32()] = mBuilder.CreatePointerCast(value,type);
                }
                break;

                case 1011:
                {
                    llvm::Value* value = values[current->readInt32()];
                    llvm::Type* type = readType(*current);
                    values[current->readInt32()] = mBuilder.CreateIntCast(value,type,true);
                }
                break;

                case 1050:
                {
                    llvm::Type* type = readType(*current);
                    values[current->readInt32()] = mBuilder.CreateAlloca(type);
                }
                break;

                case 2000:
                    mBuilder.CreateRet(values[current->readInt32()]);
                break;

                case 2001:
                    mBuilder.CreateRetVoid();
                break;

                case 3000:
                {
                    int id = current->readInt32();
                    values[current->readInt32()] = mGlobalVars[id];
                }
                break;

                case 3001:
                {
                    std::string txt = current->readString();
                    values[current->readInt32()] = mBuilder.CreateGlobalString(llvm::StringRef(txt));
                }
                break;

                case 10000:
                    printType(values[current->readInt32()]->getType());
                break;

                default:
                    std::cout<<"Wrong op type "<<opcode<<std::endl;
                break;

            }
        }

    }

}

llvm::Type* CodeGen::readType(FormatReader& reader)
{
    llvm::Type* result = nullptr;

    TypePrimitive type = (TypePrimitive) reader.readInt32();
    size_t ptrLevel = reader.readInt32();
    size_t id = reader.readInt32();

    if(type == TypePrimitive::INT1)
        result = llvm::Type::getInt1Ty(mContext);
    else if(type == TypePrimitive::INT8)
        result = llvm::Type::getInt8Ty(mContext);
    else if(type == TypePrimitive::INT16)
        result = llvm::Type::getInt16Ty(mContext);
    else if(type == TypePrimitive::INT32)
        result = llvm::Type::getInt32Ty(mContext);
    else if(type == TypePrimitive::INT64)
        result = llvm::Type::getInt64Ty(mContext);
    else if(type == TypePrimitive::FLOAT)
        result = llvm::Type::getFloatTy(mContext);
    else if(type == TypePrimitive::DOUBLE)
        result = llvm::Type::getDoubleTy(mContext);
    else if(type == TypePrimitive::VOID)
        result = llvm::Type::getVoidTy(mContext);
    else if(type == TypePrimitive::STRUCT)
    {
        result = mStructTypes[id];
    }
    else
        std::cout<<"Unknown primitive type with type # "<<type<<std::endl;

    for(size_t i = 0;i < ptrLevel;++i)
        result = result->getPointerTo();

    return result;
}

llvm::GlobalValue::LinkageTypes CodeGen::readLinkage(FormatReader& reader)
{
    int linkType = reader.readInt32();
    llvm::GlobalValue::LinkageTypes link;
    if(linkType == 1)
        link = llvm::GlobalValue::InternalLinkage;
    else
        link = llvm::GlobalValue::ExternalLinkage;
    return link;
}

void CodeGen::printType(llvm::Type* type)
{
    std::string type_str;
    llvm::raw_string_ostream rso(type_str);
    type->print(rso);
    std::cout<<rso.str()<<std::endl;
}

bool CodeGen::isDecimalType(llvm::Value* value)
{
    return isDecimalType(value->getType());
}

bool CodeGen::isDecimalType(llvm::Type* type)
{
    return type == llvm::Type::getFloatTy(mContext) || type == llvm::Type::getDoubleTy(mContext);
}
