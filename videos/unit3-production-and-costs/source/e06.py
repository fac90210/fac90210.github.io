from lib import *
class E06(Ep):
    chap = 1
    def construct(self):
        mcq(self, "Assume the marginal product of labor first rises, reaches a maximum, and then falls. If the average product of labor is falling, which of the following is true?",
            ["The marginal product of labor is greater than the average product of labor.",
             "The level of output produced must be at its maximum.",
             "The marginal product of labor must be falling.",
             "The marginal product of labor must be negative.",
             "The average product of labor has not yet reached its maximum."],
            2,
            "Average product only falls when MP is below it, and MP peaks before AP does. So by the time AP is falling, MP has to be falling too. It doesn't have to be negative yet.",
            "Quick check time. Here's a multiple choice question in the style of the AP exam. Assume marginal product first rises, peaks, then falls. If average product is falling, which statement must be true? Pause the video and pick your answer.",
            "The answer is C. If average product is falling, we're already past its maximum, which means marginal product is below average product. And since marginal product peaks before average product does, it has to be falling by now. It doesn't need to be negative, though. Average product can fall while marginal product is still positive.")
