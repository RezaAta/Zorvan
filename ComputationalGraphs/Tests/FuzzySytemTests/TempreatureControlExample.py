from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Core.GraphProcessor import GraphProcessor
from ComputationalGraphs.Core.DrawioIO import DrawioIO
from ComputationalGraphs.Nodes import (
    MinNode,
    MaxNode,
    DisplayNode,
    PiecewiseLinearNode,
    MultiplicationNode,
    DivisionNode,
    AdditionNode
    )

graph = Graph()
graphProccessor = GraphProcessor(graph, verbose = True)

humidityInputNode = DisplayNode("Humidity", value = 80)
temperatureInputNode = DisplayNode("Tempreature", value = 44)
graph.AddNode(temperatureInputNode,humidityInputNode)

hotTempreatureNode = PiecewiseLinearNode("hot tempreature",xs=[-20, 5, 25, 45, 100], mus=[0.0, 0.0, 0.5, 1.0, 1.0])
hotTempreatureNode.AddPreNode(temperatureInputNode)

coldTempreatureNode = PiecewiseLinearNode("cold tempreature",xs=[-20, 5, 25, 45, 100], mus=[1.0, 1.0, 0.5, 0.0, 0.0])
coldTempreatureNode.AddPreNode(temperatureInputNode)

highHumidity = PiecewiseLinearNode("high humidity",xs=[0, 25, 50, 75, 100], mus=[0.0, 0.0, 0.5, 1.0, 1.0])
highHumidity.AddPreNode(humidityInputNode)

lowHumidity = PiecewiseLinearNode("low humidity",xs=[0, 25, 50, 75, 100], mus=[1.0, 1.0, 0.5, 0.0, 0.0])
lowHumidity.AddPreNode(humidityInputNode)

graph.AddNode(hotTempreatureNode,coldTempreatureNode,highHumidity,lowHumidity)

hotandhigh = MinNode("hot and high")
hotandhigh.AddPreNode(hotTempreatureNode, highHumidity)

hotandlow = MinNode("hot and low")
hotandlow.AddPreNode(hotTempreatureNode, lowHumidity)

coldandhigh = MinNode("cold and high")
coldandhigh.AddPreNode(coldTempreatureNode, highHumidity)

coldandlow = MinNode("cold and low")
coldandlow.AddPreNode(coldTempreatureNode, lowHumidity)

graph.AddNode(hotandhigh, hotandlow, coldandhigh, coldandlow)

hotandlowOrcoldandhigh = MaxNode("hot and low or cold and high")
hotandlowOrcoldandhigh.AddPreNode(hotandlow, coldandhigh)
graph.AddNode(hotandlowOrcoldandhigh)


highSpeed = DisplayNode("High Speed", 100)
moderateSpeed = DisplayNode("Moderate Speed", 50)
lowSpeed = DisplayNode("Low Speed", 25)
graph.AddNode(highSpeed, moderateSpeed, lowSpeed)

aH= MultiplicationNode("aH", 0.0)
aH.AddPreNode(hotandhigh, highSpeed)
aM = MultiplicationNode("aM", 0.0)
aM.AddPreNode(hotandlowOrcoldandhigh, moderateSpeed)
aL = MultiplicationNode("aL", 0.0)
aL.AddPreNode(coldandlow, lowSpeed)
graph.AddNode(aH, aM, aL)

numinator = AdditionNode("Numerator", 0.0)
numinator.AddPreNode(aH, aM, aL)

denuminator = AdditionNode("Denominator", 0.0)
denuminator.AddPreNode(hotandhigh, hotandlowOrcoldandhigh, coldandlow)
fanspeed = DivisionNode("Fanspeed", 0.0)
fanspeed.AddPreNode(numinator, denuminator)
graph.AddNode(numinator, denuminator, fanspeed)

graphProccessor.ComputeGraphSingleThread(10)
graph.DisplayGraph("Temperature Control Fuzzy System")

DrawioIO.save(graph, "TemperatureControlFuzzySystem.drawio")

newgraph = DrawioIO.load("TemperatureControlFuzzySystem.drawio")
graphProccessor.graph = newgraph

graphProccessor.ComputeGraphSingleThread(3)
# DrawioIO = DrawioIO().generate_template_graph("TemplateComputationalGraph.drawio")
# graph = DrawioIO.load("Fanspeed Fuzzy System.drawio")
# graphProccessor.graph = graph
# graph.DisplayGraph("Fanspeed Fuzzy System")
# graphProccessor.ComputeGraphSingleThread(10)


