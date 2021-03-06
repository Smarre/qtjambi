/****************************************************************************
**
** Copyright (C) 1992-2009 Nokia. All rights reserved.
**
** This file is part of Qt Jambi.
**
** $BEGIN_LICENSE$
** GNU Lesser General Public License Usage
** This file may be used under the terms of the GNU Lesser
** General Public License version 2.1 as published by the Free Software
** Foundation and appearing in the file LICENSE.LGPL included in the
** packaging of this file.  Please review the following information to
** ensure the GNU Lesser General Public License version 2.1 requirements
** will be met: http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
**
** In addition, as a special exception, Nokia gives you certain
** additional rights. These rights are described in the Nokia Qt LGPL
** Exception version 1.0, included in the file LGPL_EXCEPTION.txt in this
** package.
**
** GNU General Public License Usage
** Alternatively, this file may be used under the terms of the GNU
** General Public License version 3.0 as published by the Free Software
** Foundation and appearing in the file LICENSE.GPL included in the
** packaging of this file.  Please review the following information to
** ensure the GNU General Public License version 3.0 requirements will be
** met: http://www.gnu.org/copyleft/gpl.html.
** $END_LICENSE$

**
** This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
** WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
**
****************************************************************************/

package com.trolltech.examples.qtconcurrent;

import com.trolltech.qt.core.*;
import com.trolltech.qt.gui.*;

import java.util.*;

public class Map {

    public static class MyMappedFunctor implements QtConcurrent.MappedFunctor<QImage, QImage> {
        public QImage map(QImage image) {
            System.err.println("Scaling image in thread: " + Thread.currentThread());
            return image.scaled(new QSize(100, 100), Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation);
        }
    }

    public static void main(String args[])
    {

        final int imageCount = 20;

        // Create a list containing imageCount images.
        List<QImage> images = new ArrayList<QImage>();
        for (int i = 0; i < imageCount; ++i)
            images.add(new QImage(1600, 1200, QImage.Format.Format_ARGB32_Premultiplied));

        MyMappedFunctor functor = new MyMappedFunctor();
        List<QImage> thumbnails = new ArrayList<QImage>();
        QTime time = new QTime();
        time.start();
        for (int i=0; i<imageCount; ++i) {
            thumbnails.add(functor.map(images.get(i)));
        }
        System.err.println("Time without QtConcurrent: " + time.elapsed() + "ms");

        // Use QtConcurrentBlocking::mapped to apply the scale function to all the
        // images in the list.
        time.restart();
        thumbnails = QtConcurrent.blockingMapped(images, functor);
        System.err.println("Time with QtConcurrent: " + time.elapsed() + "ms");

    }

}
