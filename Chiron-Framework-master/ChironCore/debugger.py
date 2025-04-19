from interpreter import ConcreteInterpreter
from ChironAST.ChironAST import AssignmentCommand, ConditionCommand, MoveCommand, PenCommand, GotoCommand, NoOpCommand

class DebuggerInterpreter(ConcreteInterpreter):
    def __init__(self, irHandler, args):
        super().__init__(irHandler, args)
        self.irHandler = irHandler
        self.args = args
        self.breakpoints = set(range(0, len(irHandler.ir)))  # Break at every instruction
        self.debug_mode = True
        self.stepping = False
        self.initProgramContext(args.params)

    def interpret(self):
        print("Entering Debugger interpret()...")
        while self.pc < len(self.ir):
            stmt, tgt = self.ir[self.pc]

            # Pause on breakpoints or step mode
            if tgt in self.breakpoints or self.stepping:
                self.stepping = False  # Reset step flag
                self.debug_prompt(stmt, self.pc)

            print(f"Program counter: {self.pc}")
            print(f"Executing: {stmt.__class__.__name__} @ line {tgt}")

            self.sanityCheck((stmt, tgt))

            if isinstance(stmt, AssignmentCommand):
                ntgt = self.handleAssignment(stmt, tgt)
            elif isinstance(stmt, ConditionCommand):
                ntgt = self.handleCondition(stmt, tgt)
            elif isinstance(stmt, MoveCommand):
                ntgt = self.handleMove(stmt, tgt)
            elif isinstance(stmt, PenCommand):
                ntgt = self.handlePen(stmt, tgt)
            elif isinstance(stmt, GotoCommand):
                ntgt = self.handleGotoCommand(stmt, tgt)
            elif isinstance(stmt, NoOpCommand):
                ntgt = self.handleNoOpCommand(stmt, tgt)
            else:
                raise NotImplementedError("Unknown instruction: %s" % type(stmt))

            self.pc += ntgt

        self.trtl.write("End, Press ESC", font=("Arial", 15, "bold"))
        if self.args is not None and self.args.hooks:
            self.chironhook.ChironEndHook(self)
        return True

    def debug_prompt(self, stmt, tgt):
        print(f"\n Paused at line {tgt}: {stmt}")
        while True:
            cmd = input("(debug) ").strip()
            if cmd == "continue":
                break
            elif cmd == "step":
                self.stepping = True
                break
            elif cmd.startswith("print "):
                var = cmd.split(" ", 1)[1]
                print(self)
                val = self.env.get(var, "undefined")
                if val is not None:
                    print(f"{var} = {val}")
                else:
                    print(f"{var} is undefined. Available vars: {list(self.env.keys())}")
            elif cmd.startswith("break "):
                try:
                    bp = int(cmd.split(" ", 1)[1])
                    self.breakpoints.add(bp)
                    print(f"Breakpoint set at line {bp}")
                except:
                    print("Usage: break <line_number>")
            elif cmd.startswith("remove "):
                try:
                    bp = int(cmd.split(" ", 1)[1])
                    self.breakpoints.discard(bp)
                    print(f"Breakpoint removed from line {bp}")
                except:
                    print("  Usage: remove <line_number>")
            elif cmd == "list":
                print("Breakpoints:", self.breakpoints)
            elif cmd == "help":
                print("Commands:\n  step\n  continue\n  break <line>\n  remove <line>\n  print <var>\n  list\n  help")
            else:
                print("Unknown command. Type 'help' for help.")
