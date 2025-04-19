
#!/usr/bin/env python3
Release = "Chiron v1.0.4"

import json
import os
import ast
import sys
from ChironAST.builder import astGenPass
import abstractInterpretation as AI
import dataFlowAnalysis as DFA
from sbfl import testsuiteGenerator

sys.path.insert(0, "../Submission/")
sys.path.insert(0, "ChironAST/")
sys.path.insert(0, "cfg/")

import pickle
import time
import turtle
import argparse
from interpreter import *
from irhandler import *
from fuzzer import *
import sExecution as se
import cfg.cfgBuilder as cfgB
import submissionDFA as DFASub
import submissionAI as AISub
from sbflSubmission import computeRanks
import csv


def cleanup():
    pass


def stopTurtle():
    turtle.bye()


if __name__ == "__main__":
    print(Release)
    print(
        """
    ░█████╗░██╗░░██╗██╗██████╗░░█████╗░███╗░░██╗
    ██╔══██╗██║░░██║██║██╔══██╗██╔══██╗████╗░██║
    ██║░░╚═╝███████║██║██████╔╝██║░░██║██╔██╗██║
    ██║░░██╗██╔══██║██║██╔══██╗██║░░██║██║╚████║
    ╚█████╔╝██║░░██║██║██║░░██║╚█████╔╝██║░╚███║
    ░╚════╝░╚═╝░░╚═╝╚═╝░░╚═╝░╚════╝░╚═╝░░╚══╝
    """
    )

    cmdparser = argparse.ArgumentParser(description="Program Analysis Framework for ChironLang Programs.")

    cmdparser.add_argument("-p", "--ir", action="store_true", help="pretty printing the IR of a Chiron program")
    cmdparser.add_argument("-r", "--run", action="store_true", help="execute Chiron program")
    cmdparser.add_argument("-gr", "--fuzzer_gen_rand", action="store_true", help="Generate random fuzzer input seeds.")
    cmdparser.add_argument("-b", "--bin", action="store_true", help="load binary IR of a Chiron program")
    cmdparser.add_argument("-k", "--hooks", action="store_true", help="Run hooks for Kachua.")
    cmdparser.add_argument("-z", "--fuzz", action="store_true", help="Run fuzzer on a Chiron program")
    cmdparser.add_argument("-t", "--timeout", default=10, type=float, help="Timeout Parameter for Analysis")
    cmdparser.add_argument("progfl")

    def parse_params(val):
        if os.path.isfile(val):
            with open(val, "r") as f:
                return json.load(f)
        else:
            return json.loads(val)

    cmdparser.add_argument(
        "-d",
        "--params",
        default=dict(),
        type=parse_params,
        help="pass variable values as a JSON string or path to a .json file",
    )

    cmdparser.add_argument("-c", "--constparams", default=dict(), type=ast.literal_eval)
    cmdparser.add_argument("-se", "--symbolicExecution", action="store_true")
    cmdparser.add_argument("-ai", "--abstractInterpretation", action="store_true")
    cmdparser.add_argument("-dfa", "--dataFlowAnalysis", action="store_true")
    cmdparser.add_argument("-sbfl", "--SBFL", action="store_true")
    cmdparser.add_argument("-bg", "--buggy", type=str)
    cmdparser.add_argument("-vars", "--inputVarsList", type=str)
    cmdparser.add_argument("-nt", "--ntests", default=10, type=int)
    cmdparser.add_argument("-pop", "--popsize", default=100, type=int)
    cmdparser.add_argument("-cp", "--cxpb", default=1.0, type=float)
    cmdparser.add_argument("-mp", "--mutpb", default=1.0, type=float)
    cmdparser.add_argument("-cfg_gen", "--control_flow", action="store_true")
    cmdparser.add_argument("-cfg_dump", "--dump_cfg", action="store_true")
    cmdparser.add_argument("-dump", "--dump_ir", action="store_true")
    cmdparser.add_argument("-ng", "--ngen", default=100, type=int)
    cmdparser.add_argument("-vb", "--verbose", default=True, type=bool)
    cmdparser.add_argument("--debug", action="store_true")

    args = cmdparser.parse_args()
    ir = ""

    if not isinstance(args.params, dict):
        raise ValueError("Wrong type for '-d' or '--params'. Use a JSON string or filename.")

    irHandler = IRHandler(ir)

    if args.bin:
        ir = irHandler.loadIR(args.progfl)
    else:
        parseTree = getParseTree(args.progfl)
        astgen = astGenPass()
        ir = astgen.visitStart(parseTree)
        print(f"IR generated with {len(ir)} instructions")

    irHandler.setIR(ir)
    print("IR set in irHandler")

    if args.control_flow:
        cfg = cfgB.buildCFG(ir, "control_flow_graph", True)
        irHandler.setCFG(cfg)
    else:
        irHandler.setCFG(None)

    if args.dump_cfg:
        cfgB.dumpCFG(cfg, "control_flow_graph")

    if args.ir:
        irHandler.pretty_print(irHandler.ir)

    if args.abstractInterpretation:
        AISub.analyzeUsingAI(irHandler)

    if args.dataFlowAnalysis:
        irOpt = DFASub.optimizeUsingDFA(irHandler)
        irHandler.pretty_print(irHandler.ir)

    if args.dump_ir:
        irHandler.pretty_print(irHandler.ir)
        irHandler.dumpIR("optimized.kw", irHandler.ir)

    if args.symbolicExecution:
        se.symbolicExecutionMain(irHandler, args.params, args.constparams, timeLimit=args.timeout)

    if args.fuzz:
        fuzzer = Fuzzer(irHandler, args)
        cov, corpus = fuzzer.fuzz(timeLimit=args.timeout, generateRandom=args.fuzzer_gen_rand)
        print(f"Coverage : {cov.total_metric},\nCorpus:")
        for index, x in enumerate(corpus):
            print(f"\tInput {index} : {x.data}")

    if args.run:
        print("Debug mode ON" if args.debug else "▶️ Running in normal mode")
        if args.debug:
            from debugger import DebuggerInterpreter
            inptr = DebuggerInterpreter(irHandler, args)
        else:
            inptr = ConcreteInterpreter(irHandler, args)

        inptr.initProgramContext(args.params)
        print("Starting interpret loop...")
        while True:
            if inptr.interpret():
                break

        print("Program Ended.")
        print("\nPress ESCAPE to exit")
        turtle.listen()
        turtle.onkeypress(stopTurtle, "Escape")
        turtle.mainloop()
