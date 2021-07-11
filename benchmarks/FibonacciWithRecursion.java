public class FibonacciWithRecursion {

    public static int bench1(int n)
    {
        if(n == 1)
            return 0;
        else if(n == 2)
            return 1;
        else
            return bench1(n - 1) + bench1(n - 2);
    }

}
