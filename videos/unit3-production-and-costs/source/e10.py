from lib import *
class E10(Ep):
    chap = 2
    def construct(self):
        mcq(self, "In the short run, assume diminishing marginal product of labor sets in with the hiring of the second worker. Which of the following will remain constant as a firm produces more output?",
            ["Average product of labor", "Total cost", "Total fixed cost", "Total variable cost", "Marginal cost"], 2,
            "Fixed costs, like rent, are the same whether you make one unit or a thousand. Total cost, variable cost, and marginal cost all change with output, and diminishing returns pull average product down.",
            "Two quick checks on costs. First: assume diminishing marginal product of labor sets in with the second worker. Which of these stays constant as the firm produces more output? Pause and choose.",
            "The answer is C, total fixed cost. Fixed costs, like rent, are the same whether you produce one unit or a thousand. Everything else on the list changes when output changes.", secs=8)
        mcq(self, "Assume that the short-run marginal cost curve initially falls, and it then rises as quantity of output increases. Which of the following must be true?",
            ["The marginal product of labor is always falling.",
             "At every output level, the short-run marginal cost curve is always above the average variable cost curve.",
             "As output increases, the unit price of labor (the wage rate) is first falling and then rising.",
             "Initially the marginal product of labor increases but eventually marginal product of labor decreases.",
             "The average variable cost curve must always be rising."], 3,
            "MC and MP are mirror images. MC falls while MP rises, and MC rises once MP falls. MC sits below AVC while AVC is falling, and the wage rate is assumed constant.",
            "Second one. Suppose marginal cost first falls, then rises. Which statement must be true? Pause the video and think about the mirror image we just saw.",
            "The answer is D. Marginal cost and marginal product are mirror images. Marginal cost falls while marginal product is rising, and marginal cost rises once marginal product starts to fall. So marginal product must first increase, then decrease. The other options don't hold. For example, marginal cost sits below average variable cost whenever AVC is falling.", secs=10)
