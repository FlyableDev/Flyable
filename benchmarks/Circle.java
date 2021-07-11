import java.util.ArrayList;

public class Circle {

    public static void main(String[] args) {

        class CirclePoint
        {
            float x;
            float y;
            public CirclePoint(float x,float y)
            {
                this.x = x;
                this.y = y;
            }
        }

        ArrayList<CirclePoint>results = new ArrayList<CirclePoint>();
        float radius = 12.3f;
        int points = 5000000;
        float angle_by_points = (3.1415f * 2.f) / points;
        for(int e = 0;e < points;e++)
        {
            float x = (float) Math.cos(angle_by_points * e) * radius;
            float y = (float) Math.sin(angle_by_points * e) * radius;
            results.add(new CirclePoint(x,y));
        }

    }

}
